const { Client, GatewayIntentBits, EmbedBuilder, ButtonBuilder, ButtonStyle, ActionRowBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, SlashCommandBuilder, REST, Routes } = require('discord.js');
const db = require('./db');

const FORM_IMAGE = 'https://cdn.discordapp.com/attachments/1420155092874563829/1507484501562101883/f9f2318f-7bb3-49bc-9f0b-42b4834bf827.png';

let client = null;

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
  if (!token || token === 'MTUwNzQ1ODc4OTU2NDIxOTQ1Mg.GjUTZh.fG088OirA1nUVUoKVjxm_moeJ-k3ckadO7epDM') {
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
      console.error('خطأ:', err);
      const msg = '❌ حدث خطأ أثناء معالجة الطلب';
      if (interaction.deferred || interaction.replied) {
        await interaction.followUp({ content: msg, ephemeral: true });
      } else {
        await interaction.reply({ content: msg, ephemeral: true });
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
        { name: '/نشر', value: '📋 نشر نموذج التقديم في الروم (للمسؤولين)', inline: false },
        { name: '/مساعدة', value: '📚 عرض هذه القائمة', inline: false },
      )
      .setFooter({ text: 'وزارة الصحة' })
      .setTimestamp();
    return interaction.reply({ embeds: [embed], ephemeral: true });

  } else if (interaction.commandName === 'حالتي') {
    const userApps = db.applications.getByUser(interaction.user.id);
    if (!userApps.length) {
      return interaction.reply({ content: '❌ ليس لديك أي طلبات تقديم.', ephemeral: true });
    }

    const latest = userApps[userApps.length - 1];
    const statusMap = { pending: '⏳ قيد المراجعة', approved: '✅ مقبول', rejected: '❌ مرفوض' };
    const date = new Date(latest.created_at + 'Z').toLocaleString('ar-EG');

    const typeLabel = latest.type === 'ambulance' ? '🚑 إسعاف' : '📋 عام';
    const embed = new EmbedBuilder()
      .setColor(latest.status === 'approved' ? 0x28a745 : latest.status === 'rejected' ? 0xdc3545 : 0xf39c12)
      .setTitle('📋 حالة طلبك')
      .addFields(
        { name: 'الاسم', value: latest.full_name, inline: true },
        { name: 'نوع الطلب', value: typeLabel, inline: true },
        { name: 'الحالة', value: statusMap[latest.status] || latest.status, inline: true },
        { name: 'تاريخ التقديم', value: date, inline: false },
      );

    if (latest.status === 'rejected' && latest.rejection_reason) {
      embed.addFields({ name: 'سبب الرفض', value: latest.rejection_reason, inline: false });
    }

    return interaction.reply({ embeds: [embed], ephemeral: true });

  } else if (interaction.commandName === 'تقديم') {
    await interaction.deferReply({ ephemeral: true });

    const settings = db.settings.get();
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
          .setCustomId('open_ambulance_form')
          .setLabel('🚑 تقديم على الإسعاف')
          .setStyle(ButtonStyle.Danger)
      : new ButtonBuilder()
          .setCustomId('submissions_closed')
          .setLabel('🔒 التقديم مغلق')
          .setStyle(ButtonStyle.Secondary);

    await interaction.channel.send({
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)]
    });

    await interaction.editReply({ content: '✅ تم نشر النموذج في هذا الروم!' });

  } else if (interaction.commandName === 'نشر') {
    const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID;
    if (ADMIN_ROLE_ID && ADMIN_ROLE_ID !== 'YOUR_ADMIN_ROLE_ID_HERE') {
      if (!interaction.member.roles.cache.has(ADMIN_ROLE_ID)) {
        return interaction.reply({ content: '❌ هذا الأمر مخصص للمسؤولين فقط.', ephemeral: true });
      }
    }

    await interaction.deferReply({ ephemeral: true });

    const settings = db.settings.get();
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
          .setCustomId('open_ambulance_form')
          .setLabel('🚑 تقديم على الإسعاف')
          .setStyle(ButtonStyle.Danger)
      : new ButtonBuilder()
          .setCustomId('submissions_closed')
          .setLabel('🔒 التقديم مغلق')
          .setStyle(ButtonStyle.Secondary);

    await interaction.channel.send({
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)]
    });

    await interaction.editReply({ content: '✅ تم نشر النموذج في هذا الروم!' });
  }
}

async function handleModalSubmit(interaction) {
  if (interaction.customId === 'application_form') {
    const full_name = interaction.fields.getTextInputValue('full_name');
    const age = interaction.fields.getTextInputValue('age');
    const reason = interaction.fields.getTextInputValue('reason');

    if (isNaN(age) || parseInt(age) < 1 || parseInt(age) > 150) {
      return interaction.reply({ content: '❌ العمر يجب أن يكون رقماً صحيحاً بين 1 و 150', ephemeral: true });
    }

    await interaction.deferReply({ ephemeral: true });

    const app = db.applications.create({
      full_name, age: parseInt(age), reason,
      discord_user_id: interaction.user.id,
      discord_username: interaction.user.username
    });

    db.logs.create({
      application_id: app.id, action: 'submit',
      performed_by: interaction.user.username,
      performed_by_id: interaction.user.id,
      details: `تقديم طلب جديد بواسطة ${full_name}`
    });

    await interaction.editReply({ content: '✅ تم إرسال طلبك بنجاح! سيتم مراجعته من قبل المسؤولين.' });

    await sendApplicationToDiscord(app, interaction.guild);

  } else if (interaction.customId === 'ambulance_form') {
    const full_name = interaction.fields.getTextInputValue('full_name');
    const age = interaction.fields.getTextInputValue('age');
    const reason = interaction.fields.getTextInputValue('reason');

    if (isNaN(age) || parseInt(age) < 1 || parseInt(age) > 150) {
      return interaction.reply({ content: '❌ العمر يجب أن يكون رقماً صحيحاً بين 1 و 150', ephemeral: true });
    }

    await interaction.deferReply({ ephemeral: true });

    const app = db.applications.create({
      type: 'ambulance', full_name, age: parseInt(age), reason,
      discord_user_id: interaction.user.id,
      discord_username: interaction.user.username
    });

    db.logs.create({
      application_id: app.id, action: 'submit',
      performed_by: interaction.user.username,
      performed_by_id: interaction.user.id,
      details: `تقديم طلب إسعاف جديد بواسطة ${full_name}`
    });

    await interaction.editReply({ content: '✅ تم إرسال طلب الإسعاف بنجاح! سيتم مراجعته من قبل المسؤولين.' });

    await sendApplicationToDiscord(app, interaction.guild);

  } else if (interaction.customId.startsWith('reject_reason_')) {
    const appId = interaction.customId.replace('reject_reason_', '');
    const reason = interaction.fields.getTextInputValue('rejection_reason');

    const app = db.applications.getById(appId);
    if (!app) return interaction.reply({ content: '❌ لم يتم العثور على الطلب.', ephemeral: true });
    if (app.status !== 'pending') return interaction.reply({ content: '❌ تم معالجة هذا الطلب بالفعل.', ephemeral: true });

    const guild = client.guilds.cache.get(process.env.GUILD_ID);
    const channel = guild?.channels.cache.get(process.env.REQUESTS_CHANNEL_ID);

    db.applications.update(appId, {
      status: 'rejected',
      rejection_reason: reason,
      reviewed_by: interaction.user.tag,
      reviewed_by_id: interaction.user.id,
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
    });

    db.logs.create({
      application_id: appId, action: 'reject',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم رفض طلب ${app.full_name} بواسطة ${interaction.user.tag} بسبب: ${reason}`
    });

    const logsChannel = guild?.channels.cache.get(process.env.LOGS_CHANNEL_ID);
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
        await msg.edit({ embeds: [embed], components: [] });
      }
    }

    await interaction.reply({ content: '❌ تم رفض الطلب.', ephemeral: true });
  }
}

async function sendApplicationToDiscord(application, guild) {
  if (!client || !client.isReady()) return;

  const channel = guild.channels.cache.get(process.env.REQUESTS_CHANNEL_ID);
  if (!channel) return;

  const user = await client.users.fetch(application.discord_user_id).catch(() => null);

  const isAmbulance = application.type === 'ambulance';
  const embed = new EmbedBuilder()
    .setColor(isAmbulance ? 0xe74c3c : 0x3498db)
    .setTitle(isAmbulance ? '🚑 طلب تقديم إسعاف جديد' : '📋 طلب تقديم جديد')
    .setThumbnail(user?.displayAvatarURL() || (isAmbulance ? 'https://cdn-icons-png.flaticon.com/512/3308/3308395.png' : 'https://cdn-icons-png.flaticon.com/512/3308/3308395.png'))
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

  await channel.send({ embeds: [embed], components: [row] });
}

async function sendPersistentForm() {
  if (!client || !client.isReady()) return;
  const channelId = process.env.FORM_CHANNEL_ID;
  if (!channelId || channelId === 'YOUR_FORM_CHANNEL_ID_HERE') return;
  const channel = client.channels.cache.get(channelId);
  if (!channel) return;

  const messages = await channel.messages.fetch({ limit: 20 });
  const old = messages.find(m => m.author.id === client.user.id && m.components.length > 0);
  if (old) await old.delete().catch(() => {});

  const settings = db.settings.get();
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
        .setCustomId('open_ambulance_form')
        .setLabel('🚑 تقديم على الإسعاف')
        .setStyle(ButtonStyle.Danger)
    : new ButtonBuilder()
        .setCustomId('submissions_closed')
        .setLabel('🔒 التقديم مغلق')
        .setStyle(ButtonStyle.Secondary);

  await channel.send({
    embeds: [embed],
    components: [new ActionRowBuilder().addComponents(btn)]
  });
}

async function sendControlPanel() {
  if (!client || !client.isReady()) return;
  const channelId = process.env.CONTROL_CHANNEL_ID;
  if (!channelId || channelId === 'YOUR_CONTROL_CHANNEL_ID_HERE') return;
  const channel = client.channels.cache.get(channelId);
  if (!channel) return;

  const messages = await channel.messages.fetch({ limit: 20 });
  const old = messages.find(m => m.author.id === client.user.id && m.components.length > 0);
  if (old) await old.delete().catch(() => {});

  const settings = db.settings.get();
  const embed = new EmbedBuilder()
    .setColor(0xd4af37)
    .setTitle('⚙️ لوحة التحكم - فتح وغلاق التقديم')
    .setDescription(
      '**الحالة الحالية:** ' + (settings.submissions_open ? '✅ **مفتوح**' : '🔒 **مغلق**') +
      '\n\nاضغط على الزر أدناه لتغيير حالة التقديم.\n\n' +
      '> 🛡️ هذا الإجراء مخصص **للمسؤولين** فقط'
    )
    .setFooter({ text: 'وزارة الصحة' })
    .setTimestamp();

  const toggleBtn = new ButtonBuilder()
    .setCustomId('toggle_submissions')
    .setLabel(settings.submissions_open ? '🔒 إغلاق التقديم' : '✅ فتح التقديم')
    .setStyle(settings.submissions_open ? ButtonStyle.Danger : ButtonStyle.Success);

  await channel.send({ embeds: [embed], components: [new ActionRowBuilder().addComponents(toggleBtn)] });
}

async function handleButtonInteraction(interaction) {
  const { customId, guild, member } = interaction;
  const ACTIVATED_ROLE_ID = process.env.ACTIVATED_ROLE_ID;
  const ADMIN_ROLE_ID = process.env.ADMIN_ROLE_ID;

  if (customId === 'open_form') {
    const settings = db.settings.get();
    if (!settings.submissions_open) {
      return interaction.reply({ content: 'شكرًا لاهتمامك ❤️\nالتقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲', ephemeral: true });
    }

    if (ACTIVATED_ROLE_ID && ACTIVATED_ROLE_ID !== 'YOUR_ACTIVATED_ROLE_ID_HERE') {
      if (!member.roles.cache.has(ACTIVATED_ROLE_ID)) {
        return interaction.reply({ content: '❌ يجب أن تمتلك رتبة **مفعل** لتتمكن من التقديم.', ephemeral: true });
      }
    }

    const userApps = db.applications.getByUser(interaction.user.id);
    if (userApps.some(a => a.status === 'pending')) {
      return interaction.reply({ content: '❌ لديك طلب قيد المراجعة بالفعل.', ephemeral: true });
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

  if (customId === 'open_ambulance_form') {
    const settings = db.settings.get();
    if (!settings.submissions_open) {
      return interaction.reply({ content: 'شكرًا لاهتمامك ❤️\nالتقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲', ephemeral: true });
    }

    if (ACTIVATED_ROLE_ID && ACTIVATED_ROLE_ID !== 'YOUR_ACTIVATED_ROLE_ID_HERE') {
      if (!member.roles.cache.has(ACTIVATED_ROLE_ID)) {
        return interaction.reply({ content: '❌ يجب أن تمتلك رتبة **مفعل** لتتمكن من التقديم.', ephemeral: true });
      }
    }

    const userApps = db.applications.getByUser(interaction.user.id);
    if (userApps.some(a => a.status === 'pending')) {
      return interaction.reply({ content: '❌ لديك طلب قيد المراجعة بالفعل.', ephemeral: true });
    }

    const modal = new ModalBuilder()
      .setCustomId('ambulance_form')
      .setTitle('🚑 نموذج التقديم - الإسعاف');

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
    return interaction.reply({ content: 'شكرًا لاهتمامك ❤️\nالتقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريبًا إن شاء الله 🤲', ephemeral: true });
  }

  if (customId === 'toggle_submissions') {
    if (!member.roles.cache.has(ADMIN_ROLE_ID)) {
      return interaction.reply({ content: '❌ ليس لديك صلاحية للقيام بهذا الإجراء.', ephemeral: true });
    }
    const settings = db.settings.get();
    const newValue = !settings.submissions_open;
    db.settings.update('submissions_open', newValue);
    await sendControlPanel();
    await sendPersistentForm();
    await interaction.reply({ content: newValue ? '✅ تم فتح التقديم!' : '🔒 تم إغلاق التقديم!', ephemeral: true });
    return;
  }

  if (!member.roles.cache.has(ADMIN_ROLE_ID)) {
    return interaction.reply({ content: '❌ ليس لديك صلاحية للقيام بهذا الإجراء.', ephemeral: true });
  }

  if (customId.startsWith('approve_')) {
    const appId = customId.replace('approve_', '');
    const app = db.applications.getById(appId);
    if (!app) return interaction.reply({ content: '❌ لم يتم العثور على الطلب.', ephemeral: true });
    if (app.status !== 'pending') return interaction.reply({ content: '❌ تم معالجة هذا الطلب بالفعل.', ephemeral: true });

    db.applications.update(appId, {
      status: 'approved',
      reviewed_by: interaction.user.tag,
      reviewed_by_id: interaction.user.id,
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
    });

    db.logs.create({
      application_id: appId, action: 'approve',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم قبول طلب ${app.full_name} بواسطة ${interaction.user.tag}`
    });

    const logsChannel = guild.channels.cache.get(process.env.LOGS_CHANNEL_ID);
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
      } catch (err) {
        console.error('خطأ في إرسال إشعار:', err);
      }
    }

    const embed = EmbedBuilder.from(interaction.message.embeds[0])
      .setColor(0x28a745)
      .setTitle('✅ تم قبول الطلب')
      .addFields({ name: 'تمت الموافقة بواسطة', value: interaction.user.tag })
      .setFooter({ text: `تم القبول في ${new Date().toLocaleString('ar-EG')}` });

    await interaction.message.edit({ embeds: [embed], components: [] });
    await interaction.reply({ content: '✅ تم قبول الطلب بنجاح!', ephemeral: true });

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
