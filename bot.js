const { Client, GatewayIntentBits, EmbedBuilder, ButtonBuilder, ButtonStyle, ActionRowBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, SlashCommandBuilder, REST, Routes, MessageFlags } = require('discord.js');
const db = require('./db');

const FORM_IMAGE = 'https://cdn.discordapp.com/attachments/1420155092874563829/1507484501562101883/f9f2318f-7bb3-49bc-9f0b-42b4834bf827.png';

let client = null;

async function resolveTextChannel(guild, channelId, label) {
  if (!guild) {
    console.error(`❌ لا يمكن استخدام الروم ${label} لأن البوت غير مرتبط بمجموعة Discord.`);
    return null;
  }

  let channel = guild.channels.cache.get(channelId);
  if (!channel) {
    try {
      channel = await guild.channels.fetch(channelId);
    } catch (err) {
      console.error(`❌ فشل جلب ${label} (${channelId}):`, err.message || err);
      return null;
    }
  }

  if (!channel || !channel.isTextBased()) {
    console.error(`❌ ${label} (${channelId}) ليس روم نصي صالحًا.`);
    return null;
  }

  return channel;
}

async function findPersistentFormMessage(channel) {
  const messages = await channel.messages.fetch({ limit: 30 });
  return messages.find(m =>
    m.author.id === client.user.id &&
    m.embeds.some(embed => embed.title === '📋 نموذج التقديم - وزارة الصحة')
  ) || messages.find(m => m.author.id === client.user.id && m.components.length > 0);
}

function buildControlPanelPayload(settings) {
  const CONTROL_IMAGE = 'https://cdn.discordapp.com/attachments/1420155092874563827/1507566493863510036/6a06818e-cbbb-4e21-ae2d-b881781ea41b.png?ex=6a125e35&is=6a110cb5&hm=719cc88e347a8e6bf573afd3876804338a43a70296b75fe3d0449326aa17ba4f';
  const embed = new EmbedBuilder()
    .setColor(0xd4af37)
    .setTitle('⚙️ لوحة التحكم - فتح وغلاق التقديم')
    .setImage(CONTROL_IMAGE)
    .setFooter({ text: 'وزارة الصحة' })
    .setTimestamp();

  const toggleBtn = new ButtonBuilder()
    .setCustomId('toggle_submissions')
    .setLabel(settings.submissions_open ? '🔒 إغلاق التقديم' : '✅ فتح التقديم')
    .setStyle(settings.submissions_open ? ButtonStyle.Danger : ButtonStyle.Success);

  return { embeds: [embed], components: [new ActionRowBuilder().addComponents(toggleBtn)] };
}

async function postControlPanelToChannel(channel, settings = null) {
  if (!channel) return false;

  const currentSettings = settings || await db.settings.get();
  const payload = buildControlPanelPayload(currentSettings);
  const messages = await channel.messages.fetch({ limit: 30 });
  const old = messages.find(m =>
    m.author.id === client.user.id &&
    m.embeds.some(embed => embed.title === '⚙️ لوحة التحكم - فتح وغلاق التقديم')
  );

  if (old) {
    await old.edit(payload).catch(() => {});
    return true;
  }

  await channel.send(payload);
  return true;
}

function initializeBot() {
  client = new Client({
    intents: [
      GatewayIntentBits.Guilds,
      GatewayIntentBits.GuildMessages,
      GatewayIntentBits.MessageContent,
      GatewayIntentBits.GuildMembers,
    ]
  });

  const token = process.env.BOT_TOKEN;
  if (!token) {
    console.warn('⚠️ لم يتم تعيين توكن البوت. البوت لن يعمل.');
    return null;
  }

  client.once('ready', async () => {
    console.log(`✅ البوت متصل كـ ${client.user.tag}`);
    await registerCommands();
    await sendPersistentForm();
    await sendControlPanel();
  });

  client.on('interactionCreate', async (interaction) => {
    try {
      if (interaction.isChatInputCommand()) {
        await handleCommand(interaction);
      } else if (interaction.isModalSubmit()) {
        await handleModalSubmit(interaction);
      } else if (interaction.isButton()) {
        await handleButtonInteraction(interaction);
      }
    } catch (err) {
      const type = interaction.isChatInputCommand() ? 'command' : interaction.isButton() ? 'button' : interaction.isModalSubmit() ? 'modal' : 'other';
      const id = interaction.customId || interaction.commandName || '?';
      console.error(`❌ خطأ [${type}] [${id}]:`, err.message || err);
      const msg = { content: '❌ حدث خطأ أثناء معالجة الطلب', flags: MessageFlags.Ephemeral };
      if (interaction.deferred || interaction.replied) {
        await interaction.followUp(msg).catch(() => {});
      } else {
        await interaction.reply(msg).catch(() => {});
      }
    }
  });

  client.login(token);
  return client;
}

async function registerCommands() {
  const GUILD_ID = process.env.GUILD_ID;
  if (!GUILD_ID || GUILD_ID === 'YOUR_GUILD_ID_HERE') return;

  const commands = [
    new SlashCommandBuilder()
      .setName('تقديم')
      .setDescription('📋 عرض نموذج التقديم'),
    new SlashCommandBuilder()
      .setName('حالتي')
      .setDescription('🔍 عرض حالة طلب التقديم الخاص بك'),
    new SlashCommandBuilder()
      .setName('مساعدة')
      .setDescription('📚 عرض قائمة الأوامر المتاحة'),
    new SlashCommandBuilder()
      .setName('نشر')
      .setDescription('📋 نشر نموذج التقديم في الروم الحالي (للمسؤولين)'),
    new SlashCommandBuilder()
      .setName('لوحة_التحكم')
      .setDescription('⚙️ نشر لوحة التحكم في الروم الحالي (للمسؤولين)'),
  ];

  const rest = new REST({ version: '10' }).setToken(process.env.BOT_TOKEN);
  try {
    await rest.put(Routes.applicationGuildCommands(client.user.id, GUILD_ID), {
      body: commands.map(c => c.toJSON())
    });
    console.log('✅ تم تسجيل الأوامر');
  } catch (err) {
    console.error('خطأ في تسجيل الأوامر:', err);
  }
}

async function handleCommand(interaction) {
  if (interaction.commandName === 'مساعدة') {
    const embed = new EmbedBuilder()
      .setColor(0xd4af37)
      .setTitle('📚 قائمة الأوامر')
      .setDescription('الأوامر المتاحة في بوت وزارة الصحة')
      .addFields(
        { name: '📋 الزر في الروم', value: 'اضغط على زر **تقديم طلب** في روم النموذج', inline: false },
        { name: '/تقديم', value: '📋 عرض نموذج التقديم في الروم الحالي', inline: false },
        { name: '/حالتي', value: '🔍 عرض حالة طلب التقديم الخاص بك', inline: false },
        { name: '/لوحة_التحكم', value: '⚙️ نشر لوحة التحكم في الروم الحالي (للمسؤولين)', inline: false },
        { name: '/مساعدة', value: '📚 عرض هذه القائمة', inline: false },
      )
      .setFooter({ text: 'وزارة الصحة' })
      .setTimestamp();
    return interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });

  } else if (interaction.commandName === 'حالتي') {
    const userApps = await db.applications.getByUser(interaction.user.id);
    if (!userApps.length) {
      return interaction.reply({ content: '❌ ليس لديك أي طلبات تقديم.', flags: MessageFlags.Ephemeral });
    }

    const latest = userApps[userApps.length - 1];
    const statusMap = { pending: '⏳ قيد المراجعة', approved: '✅ مقبول', rejected: '❌ مرفوض' };
    const date = new Date(latest.created_at + 'Z').toLocaleString('ar-EG');

    const embed = new EmbedBuilder()
      .setColor(latest.status === 'approved' ? 0x28a745 : latest.status === 'rejected' ? 0xdc3545 : 0xf39c12)
      .setTitle('📋 حالة طلبك')
      .addFields(
        { name: 'الاسم', value: latest.full_name, inline: true },
        { name: 'الحالة', value: statusMap[latest.status] || latest.status, inline: true },
        { name: 'تاريخ التقديم', value: date, inline: false },
      );

    if (latest.status === 'rejected' && latest.rejection_reason) {
      embed.addFields({ name: 'سبب الرفض', value: latest.rejection_reason, inline: false });
    }

    return interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });

  } else if (interaction.commandName === 'تقديم') {
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const settings = await db.settings.get();
    const embed = new EmbedBuilder()
      .setColor(0xd4af37)
      .setTitle('📋 نموذج التقديم - وزارة الصحة')
      .setDescription(
        (settings.submissions_open
          ? 'اضغط على الزر أدناه لتقديم طلب جديد.'
          : 'التقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲') +
        '\n\n**━━━ ⚠️ الشــــروط ⚠️ ━━━**\n' +
        '**• يجب أن يكون عمرك فوق 15 سنة ✅**\n' +
        '**• يمكنك تقديم طلب واحد فقط كل مرة 📄**\n' +
        '**• بعد المراجعة سيتم إعلامك بنتيجة طلبك 📬**'
      )
      .setImage(FORM_IMAGE)
      .setFooter({ text: 'وزارة الصحة' })
      .setTimestamp();

    const btn = settings.submissions_open
      ? new ButtonBuilder()
          .setCustomId('open_form')
          .setLabel('📋 تقديم طلب')
          .setStyle(ButtonStyle.Success)
      : new ButtonBuilder()
          .setCustomId('submissions_closed')
          .setLabel('🔒 التقديم مغلق')
          .setStyle(ButtonStyle.Danger);

    await interaction.channel.send({
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)]
    });

    await interaction.editReply({ content: '✅ تم نشر النموذج في هذا الروم!' });

  } else if (interaction.commandName === 'نشر') {
    const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID;
    if (ADMIN_ROLE_ID && ADMIN_ROLE_ID !== 'YOUR_ADMIN_ROLE_ID_HERE') {
      if (!interaction.member.roles.cache.has(ADMIN_ROLE_ID)) {
        return interaction.reply({ content: '❌ هذا الأمر مخصص للمسؤولين فقط.', flags: MessageFlags.Ephemeral });
      }
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const settings = await db.settings.get();
    const embed = new EmbedBuilder()
      .setColor(0xd4af37)
      .setTitle('📋 نموذج التقديم - وزارة الصحة')
      .setDescription(
        (settings.submissions_open
          ? 'اضغط على الزر أدناه لتقديم طلب جديد.'
          : 'التقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲') +
        '\n\n**━━━ ⚠️ الشــــروط ⚠️ ━━━**\n' +
        '**• يجب أن يكون عمرك فوق 15 سنة ✅**\n' +
        '**• يمكنك تقديم طلب واحد فقط كل مرة 📄**\n' +
        '**• بعد المراجعة سيتم إعلامك بنتيجة طلبك 📬**'
      )
      .setImage(FORM_IMAGE)
      .setFooter({ text: 'وزارة الصحة' })
      .setTimestamp();

    const btn = settings.submissions_open
      ? new ButtonBuilder()
          .setCustomId('open_form')
          .setLabel('📋 تقديم طلب')
          .setStyle(ButtonStyle.Success)
      : new ButtonBuilder()
          .setCustomId('submissions_closed')
          .setLabel('🔒 التقديم مغلق')
          .setStyle(ButtonStyle.Danger);

    await interaction.channel.send({
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)]
    });

    await interaction.editReply({ content: '✅ تم نشر النموذج في هذا الروم!' });
  } else if (interaction.commandName === 'لوحة_التحكم') {
    const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID;
    if (ADMIN_ROLE_ID && ADMIN_ROLE_ID !== 'YOUR_ADMIN_ROLE_ID_HERE') {
      if (!interaction.member.roles.cache.has(ADMIN_ROLE_ID)) {
        return interaction.reply({ content: '❌ هذا الأمر مخصص للمسؤولين فقط.', flags: MessageFlags.Ephemeral });
      }
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    await postControlPanelToChannel(interaction.channel);
    await interaction.editReply({ content: '✅ تم نشر لوحة التحكم في هذا الروم!' });
  }
}

async function handleModalSubmit(interaction) {
  if (interaction.customId === 'application_form') {
    const full_name = interaction.fields.getTextInputValue('full_name');
    const age = interaction.fields.getTextInputValue('age');
    const reason = interaction.fields.getTextInputValue('reason');

    if (isNaN(age) || parseInt(age) < 16 || parseInt(age) > 150) {
      return interaction.reply({ content: '❌ العمر يجب أن يكون رقماً صحيحاً فوق 15 سنة', flags: MessageFlags.Ephemeral });
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const app = await db.applications.create({
      full_name, age: parseInt(age), reason,
      discord_user_id: interaction.user.id,
      discord_username: interaction.user.username
    });

    await db.logs.create({
      application_id: app.id, action: 'submit',
      performed_by: interaction.user.username,
      performed_by_id: interaction.user.id,
      details: `تقديم طلب جديد بواسطة ${full_name}`
    });

    await interaction.editReply({ content: '✅ تم إرسال طلبك بنجاح! سيتم مراجعته من قبل المسؤولين.' });

    await sendApplicationToDiscord(app, interaction.guild);

  } else if (interaction.customId.startsWith('reject_reason_')) {
    const appId = interaction.customId.replace('reject_reason_', '');
    const reason = interaction.fields.getTextInputValue('rejection_reason');

    const app = await db.applications.getById(appId);
    if (!app) return interaction.reply({ content: '❌ لم يتم العثور على الطلب.', flags: MessageFlags.Ephemeral });
    if (app.status !== 'pending') return interaction.reply({ content: '❌ تم معالجة هذا الطلب بالفعل.', flags: MessageFlags.Ephemeral });

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const guild = client.guilds.cache.get(process.env.GUILD_ID);
    let channel = guild?.channels.cache.get(process.env.REQUESTS_CHANNEL_ID);
    if (!channel) {
      try {
        channel = await guild?.channels.fetch(process.env.REQUESTS_CHANNEL_ID);
      } catch (err) {
        console.error('فشل جلب رو الطلبات:', err);
      }
    }

    await db.applications.update(appId, {
      status: 'rejected',
      rejection_reason: reason,
      reviewed_by: interaction.user.tag,
      reviewed_by_id: interaction.user.id,
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
    });

    await db.logs.create({
      application_id: appId, action: 'reject',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم رفض طلب ${app.full_name} بواسطة ${interaction.user.tag} بسبب: ${reason}`
    });

    let logsChannel = guild?.channels.cache.get(process.env.LOGS_CHANNEL_ID);
    if (!logsChannel) {
      try {
        logsChannel = await guild?.channels.fetch(process.env.LOGS_CHANNEL_ID);
      } catch (err) {
        console.error('فشل جلب رو السجلات:', err);
      }
    }
    if (logsChannel) {
      const logEmbed = new EmbedBuilder()
        .setColor(0xdc3545)
        .setTitle('❌ رفض طلب')
        .setDescription(
          `━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `**📋 المعلومات**\n` +
          `**👤 الاسم:** ${app.full_name}\n` +
          `**🆔 المعرف:** \`${app.id}\`\n` +
          `**📊 الحالة:** ❌ مرفوض\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `**🔍 تفاصيل الرفض**\n` +
          `**👮 بواسطة:** ${interaction.user.tag}\n` +
          `**📝 السبب:** ${reason}`
        )
        .setFooter({ text: 'وزارة الصحة' })
        .setTimestamp();
      await logsChannel.send({ embeds: [logEmbed] });
    }

    if (app.discord_user_id) {
      try {
        const targetMember = await guild.members.fetch(app.discord_user_id);
        const notifyEmbed = new EmbedBuilder()
          .setColor(0xdc3545)
          .setTitle('❌ تم رفض طلبك')
          .setDescription(`عذراً ${app.full_name}، تم رفض طلب التقديم الخاص بك.`)
          .addFields({ name: 'السبب', value: reason })
          .setFooter({ text: 'وزارة الصحة' })
          .setTimestamp();
        await targetMember.send({ embeds: [notifyEmbed] }).catch(() => {});
      } catch (err) {
        console.error('خطأ في إرسال إشعار:', err);
      }
    }

    if (channel) {
      const msg = (await channel.messages.fetch({ limit: 20 })).find(m =>
        m.embeds.length && m.embeds[0].footer?.text === `معرف الطلب: ${appId}`
      );
      if (msg) {
        const embed = EmbedBuilder.from(msg.embeds[0])
          .setColor(0xdc3545)
          .setTitle('❌ تم رفض الطلب')
          .addFields(
            { name: 'تم الرفض بواسطة', value: interaction.user.tag },
            { name: 'السبب', value: reason }
          )
          .setFooter({ text: `تم الرفض في ${new Date().toLocaleString('ar-EG')}` });
        await msg.edit({ embeds: [embed], components: [] }).catch(err => console.error('فشل تعديل رسالة الرفض:', err));
      }
    }

    await interaction.editReply({ content: '❌ تم رفض الطلب.' });
  }
}

async function sendApplicationToDiscord(application, guild) {
  if (!client || !client.isReady()) {
    console.error('البوت غير جاهز لإرسال الطلب');
    return;
  }

  const channelId = process.env.REQUESTS_CHANNEL_ID;
  console.log(`محاولة إرسال الطلب إلى الروم: ${channelId}`);

  const channel = await resolveTextChannel(guild, channelId, 'قناة الطلبات');
  if (!channel) {
    console.error(`❌ تعذّر الوصول إلى قناة الطلبات ${channelId}.`);
    return;
  }

  const user = await client.users.fetch(application.discord_user_id).catch(() => null);

  const embed = new EmbedBuilder()
    .setColor(0x3498db)
    .setTitle('📋 طلب تقديم جديد')
    .setThumbnail(user?.displayAvatarURL() || 'https://cdn-icons-png.flaticon.com/512/3308/3308395.png')
    .addFields(
      { name: '👤 الاسم', value: application.full_name, inline: true },
      { name: '🎂 العمر', value: String(application.age), inline: true },
      { name: '📝 سبب التقديم', value: application.reason || 'غير محدد', inline: false },
      { name: '👤 مقدم الطلب', value: user ? `<@${application.discord_user_id}>` : application.discord_username, inline: true }
    )
    .setFooter({ text: `معرف الطلب: ${application.id}` })
    .setTimestamp();

  const approveBtn = new ButtonBuilder()
    .setCustomId(`approve_${application.id}`)
    .setLabel('✅ قبول')
    .setStyle(ButtonStyle.Success);

  const rejectBtn = new ButtonBuilder()
    .setCustomId(`reject_${application.id}`)
    .setLabel('❌ رفض')
    .setStyle(ButtonStyle.Danger);

  const row = new ActionRowBuilder().addComponents(approveBtn, rejectBtn);

  try {
    await channel.send({ embeds: [embed], components: [row] });
    console.log(`تم إرسال الطلب ${application.id} بنجاح إلى الروم`);
  } catch (err) {
    console.error(`فشل إرسال الطلب ${application.id} إلى الروم:`, err);
  }
}

async function sendPersistentForm() {
  if (!client || !client.isReady()) return;
  const channelId = process.env.FORM_CHANNEL_ID;
  if (!channelId || channelId === 'YOUR_FORM_CHANNEL_ID_HERE') return;

  const channel = await resolveTextChannel(client.guilds.cache.get(process.env.GUILD_ID), channelId, 'قناة النموذج');
  if (!channel) return;

  const old = await findPersistentFormMessage(channel);

  const settings = await db.settings.get();
  const embed = new EmbedBuilder()
    .setColor(0xd4af37)
    .setTitle('📋 نموذج التقديم - وزارة الصحة')
    .setDescription(
      (settings.submissions_open
        ? 'اضغط على الزر أدناه لتقديم طلب جديد.'
        : 'التقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲') +
      '\n\n**━━━ ⚠️ الشــــروط ⚠️ ━━━**\n' +
      '**• يجب أن يكون عمرك فوق 15 سنة ✅**\n' +
      '**• يمكنك تقديم طلب واحد فقط كل مرة 📄**\n' +
      '**• بعد المراجعة سيتم إعلامك بنتيجة طلبك 📬**'
    )
    .setImage(FORM_IMAGE)
    .setFooter({ text: 'وزارة الصحة' })
    .setTimestamp();

  const btn = settings.submissions_open
    ? new ButtonBuilder()
        .setCustomId('open_form')
        .setLabel('📋 تقديم طلب')
        .setStyle(ButtonStyle.Success)
    : new ButtonBuilder()
        .setCustomId('submissions_closed')
        .setLabel('🔒 التقديم مغلق')
        .setStyle(ButtonStyle.Danger);

  const payload = { embeds: [embed], components: [new ActionRowBuilder().addComponents(btn)] };

  if (old) {
    try {
      await old.edit(payload);
      return;
    } catch (err) {
      console.error('❌ فشل تحديث رسالة النموذج، سأعيد نشرها:', err.message || err);
      try {
        await old.delete().catch(() => {});
      } catch {}
    }
  }

  await channel.send(payload);
}

async function sendControlPanel() {
  if (!client || !client.isReady()) return;
  const channelId = process.env.CONTROL_CHANNEL_ID;
  if (!channelId || channelId === 'YOUR_CONTROL_CHANNEL_ID_HERE') return;

  const channel = await resolveTextChannel(client.guilds.cache.get(process.env.GUILD_ID), channelId, 'قناة التحكم');
  if (!channel) return;

  await postControlPanelToChannel(channel);
}

async function handleButtonInteraction(interaction) {
  const { customId, guild, member } = interaction;
  const ACTIVATED_ROLE_ID = process.env.ACTIVATED_ROLE_ID;
  const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID;

  if (customId === 'open_form') {
    const settings = db.fast.settings;
    if (!settings.submissions_open) {
      return interaction.reply({ content: 'شكرًا لاهتمامك ❤️\nالتقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲', flags: MessageFlags.Ephemeral });
    }

    if (ACTIVATED_ROLE_ID && ACTIVATED_ROLE_ID !== 'YOUR_ACTIVATED_ROLE_ID_HERE') {
      if (!member.roles.cache.has(ACTIVATED_ROLE_ID)) {
        return interaction.reply({ content: '❌ يجب أن تمتلك رتبة **مفعل** لتتمكن من التقديم.', flags: MessageFlags.Ephemeral });
      }
    }

    const APPROVED_ROLE_ID = process.env.APPROVED_ROLE_ID;
    if (APPROVED_ROLE_ID && APPROVED_ROLE_ID !== 'YOUR_APPROVED_ROLE_ID_HERE') {
      if (member.roles.cache.has(APPROVED_ROLE_ID)) {
        return interaction.reply({ content: '❌ لديك بالفعل رتبة **مقبول**، لا يمكنك التقديم مجدداً.', flags: MessageFlags.Ephemeral });
      }
    }

    const userApps = db.fast.getUserApps(interaction.user.id);
    if (userApps.some(a => a.status === 'pending')) {
      return interaction.reply({ content: '❌ لديك طلب قيد المراجعة بالفعل.', flags: MessageFlags.Ephemeral });
    }

    const modal = new ModalBuilder()
      .setCustomId('application_form')
      .setTitle('📋 نموذج التقديم');

    const fullName = new TextInputBuilder()
      .setCustomId('full_name').setLabel('اسمك')
      .setStyle(TextInputStyle.Short).setPlaceholder('أدخل اسمك الكامل')
      .setMaxLength(100).setRequired(true);

    const age = new TextInputBuilder()
      .setCustomId('age').setLabel('عمرك')
      .setStyle(TextInputStyle.Short).setPlaceholder('مثال: 25')
      .setMaxLength(3).setRequired(true);

    const reason = new TextInputBuilder()
      .setCustomId('reason').setLabel('سبب التقديم')
      .setStyle(TextInputStyle.Paragraph).setPlaceholder('اكتب سبب تقديمك هنا...')
      .setMaxLength(1000).setRequired(true);

    modal.addComponents(
      new ActionRowBuilder().addComponents(fullName),
      new ActionRowBuilder().addComponents(age),
      new ActionRowBuilder().addComponents(reason)
    );

    return interaction.showModal(modal);
  }

  if (customId === 'submissions_closed') {
    const CLOSED_IMAGE = 'https://cdn.discordapp.com/attachments/1420155092874563827/1507564528445948035/e55c93c4-1db1-443a-86af-ee6a0311e721.png?ex=6a125c60&is=6a110ae0&hm=fc995b702e1a0a33499232b6807f728044f7a782aab95ee370320e621c67164c';
    const embed = new EmbedBuilder()
      .setColor(0xd4af37)
      .setImage(CLOSED_IMAGE)
      .setFooter({ text: 'وزارة الصحة' })
      .setTimestamp();
    return interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
  }

  if (customId === 'toggle_submissions') {
    if (ADMIN_ROLE_ID && ADMIN_ROLE_ID !== 'YOUR_ADMIN_ROLE_ID_HERE' && !member.roles.cache.has(ADMIN_ROLE_ID)) {
      return interaction.reply({ content: '❌ ليس لديك صلاحية للقيام بهذا الإجراء.', flags: MessageFlags.Ephemeral });
    }
    
    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const settings = await db.settings.get();
    const newValue = !settings.submissions_open;
    await db.settings.update('submissions_open', newValue);

    const toggleBtn = new ButtonBuilder()
      .setCustomId('toggle_submissions')
      .setLabel(newValue ? '🔒 إغلاق التقديم' : '✅ فتح التقديم')
      .setStyle(newValue ? ButtonStyle.Danger : ButtonStyle.Success);

    try {
      await interaction.message.edit({ components: [new ActionRowBuilder().addComponents(toggleBtn)] });
    } catch (err) {
      console.error('فشل تحديث الزر:', err);
    }
    
    await sendPersistentForm();
    
    await interaction.editReply({ content: newValue ? '✅ تم فتح التقديم' : '🔒 تم إغلاق التقديم' });
    return;
  }

  if (ADMIN_ROLE_ID && ADMIN_ROLE_ID !== 'YOUR_ADMIN_ROLE_ID_HERE' && !member.roles.cache.has(ADMIN_ROLE_ID)) {
    return interaction.reply({ content: '❌ ليس لديك صلاحية للقيام بهذا الإجراء.', flags: MessageFlags.Ephemeral });
  }

  if (customId.startsWith('approve_')) {
    const appId = customId.replace('approve_', '');
    const app = await db.applications.getById(appId);
    if (!app) return interaction.reply({ content: '❌ لم يتم العثور على الطلب.', flags: MessageFlags.Ephemeral });
    if (app.status !== 'pending') return interaction.reply({ content: '❌ تم معالجة هذا الطلب بالفعل.', flags: MessageFlags.Ephemeral });

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    await db.applications.update(appId, {
      status: 'approved',
      reviewed_by: interaction.user.tag,
      reviewed_by_id: interaction.user.id,
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
    });

    await db.logs.create({
      application_id: appId, action: 'approve',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم قبول طلب ${app.full_name} بواسطة ${interaction.user.tag}`
    });

    let logsChannel = guild.channels.cache.get(process.env.LOGS_CHANNEL_ID);
    if (!logsChannel) {
      try {
        logsChannel = await guild.channels.fetch(process.env.LOGS_CHANNEL_ID);
      } catch (err) {
        console.error('فشل جلب رو السجلات:', err);
      }
    }
    if (logsChannel) {
      const logEmbed = new EmbedBuilder()
        .setColor(0x28a745)
        .setTitle('✅ قبول طلب')
        .setDescription(
          `━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `**📋 المعلومات**\n` +
          `**👤 الاسم:** ${app.full_name}\n` +
          `**🆔 المعرف:** \`${app.id}\`\n` +
          `**📊 الحالة:** ✅ مقبول\n` +
          `━━━━━━━━━━━━━━━━━━━━━━━━\n` +
          `**🔍 تفاصيل القبول**\n` +
          `**👮 بواسطة:** ${interaction.user.tag}`
        )
        .setFooter({ text: 'وزارة الصحة' })
        .setTimestamp();
      await logsChannel.send({ embeds: [logEmbed] });
    }

    if (app.discord_user_id) {
      try {
        const targetMember = await guild.members.fetch(app.discord_user_id);
        const notifyEmbed = new EmbedBuilder()
          .setColor(0x28a745)
          .setTitle('✅ تم قبول طلبك!')
          .setDescription(`مرحباً ${app.full_name}، تم قبول طلب التقديم الخاص بك.`)
          .setFooter({ text: 'وزارة الصحة' })
          .setTimestamp();
        await targetMember.send({ embeds: [notifyEmbed] }).catch(() => {});

        const approvedRoleId = process.env.APPROVED_ROLE_ID;
        if (approvedRoleId && approvedRoleId !== 'YOUR_APPROVED_ROLE_ID_HERE') {
          await targetMember.roles.add(approvedRoleId).catch(() => {});
        }
      } catch (err) {
        console.error('خطأ في إرسال إشعار أو إعطاء رتبة:', err);
      }
    }

    const embed = EmbedBuilder.from(interaction.message.embeds[0])
      .setColor(0x28a745)
      .setTitle('✅ تم قبول الطلب')
      .addFields({ name: 'تمت الموافقة بواسطة', value: interaction.user.tag })
      .setFooter({ text: `تم القبول في ${new Date().toLocaleString('ar-EG')}` });

    await interaction.message.edit({ embeds: [embed], components: [] }).catch(err => console.error('فشل تعديل رسالة القبول:', err));
    await interaction.editReply({ content: '✅ تم قبول الطلب بنجاح!' });

  } else if (customId.startsWith('reject_')) {
    const appId = customId.replace('reject_', '');

    const modal = new ModalBuilder()
      .setCustomId(`reject_reason_${appId}`)
      .setTitle('❌ رفض الطلب');

    const reasonInput = new TextInputBuilder()
      .setCustomId('rejection_reason')
      .setLabel('سبب الرفض')
      .setStyle(TextInputStyle.Paragraph)
      .setPlaceholder('اكتب سبب رفض الطلب...')
      .setMaxLength(1000)
      .setRequired(true);

    const row = new ActionRowBuilder().addComponents(reasonInput);
    modal.addComponents(row);

    await interaction.showModal(modal);
  }
}

async function refreshForm() {
  await sendPersistentForm();
}

module.exports = { initializeBot, refreshForm };
