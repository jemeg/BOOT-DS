require('dotenv').config();
const { Client, GatewayIntentBits, EmbedBuilder, ButtonBuilder, ButtonStyle, ActionRowBuilder, ModalBuilder, TextInputBuilder, TextInputStyle, SlashCommandBuilder, REST, Routes, MessageFlags, PermissionFlagsBits } = require('discord.js');
const path = require('path');
const db = require('./db');

const LOCAL_IMAGES = {
  form: path.join(__dirname, 'emg3.png'),
  control: path.join(__dirname, 'emg2.png'),
  closed: path.join(__dirname, 'emg1.png'),
  approved: path.join(__dirname, 'emg4.png'),
  rejected: path.join(__dirname, 'emg5.png'),
};

const FORM_IMAGE = 'attachment://emg3.png';

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

async function getGuildById(guildId) {
  if (!client || !client.isReady() || !guildId) {
    return null;
  }

  return client.guilds.cache.get(guildId) || (await client.guilds.fetch(guildId).catch(() => null));
}

async function getGuilds() {
  if (!client || !client.isReady()) {
    return [];
  }

  return [...client.guilds.cache.values()];
}

async function findPersistentFormMessage(channel) {
  const messages = await channel.messages.fetch({ limit: 30 });
  return messages.find(m =>
    m.author.id === client.user.id &&
    m.embeds.some(embed => embed.title === '📋 نموذج التقديم - وزارة الصحة')
  ) || messages.find(m => m.author.id === client.user.id && m.components.length > 0);
}

function buildControlPanelPayload(settings, includeFile = true) {
  const CONTROL_IMAGE = 'attachment://emg2.png';
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

  const payload = {
    embeds: [embed],
    components: [new ActionRowBuilder().addComponents(toggleBtn)],
  };

  if (includeFile) {
    payload.files = [{ attachment: LOCAL_IMAGES.control, name: 'emg2.png' }];
  }

  return payload;
}

async function postControlPanelToChannel(channel, settings = null) {
  if (!channel) return false;

  const currentSettings = settings || await db.settings.get(channel.guild.id);
  const messages = await channel.messages.fetch({ limit: 30 });
  const old = messages.find(m =>
    m.author.id === client.user.id &&
    m.embeds.some(embed => embed.title === '⚙️ لوحة التحكم - فتح وغلاق التقديم')
  );

  if (old) {
    await old.edit(buildControlPanelPayload(currentSettings, false)).catch(() => {});
    return true;
  }

  await channel.send(buildControlPanelPayload(currentSettings, true));
  return true;
}

async function canManageSettings(interaction) {
  if (!interaction.inGuild()) {
    return false;
  }

  if (interaction.memberPermissions?.has(PermissionFlagsBits.Administrator)) {
    return true;
  }

  const settings = await db.settings.get(interaction.guildId);
  if (!settings.admin_role_id) {
    return false;
  }

  return interaction.member.roles.cache.has(settings.admin_role_id);
}

function shouldIgnoreInteractionError(err) {
  const message = err?.message || '';
  return message.includes('Unknown interaction') || message.includes('Interaction has already been acknowledged.');
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
    throw new Error('⚠️ لم يتم تعيين توكن البوت في المتغيرات.');
  }

  client.once('clientReady', async () => {
    console.log(`✅ البوت متصل كـ ${client.user.tag}`);
    try {
      await registerCommands();
      await sendPersistentForm();
      await sendControlPanel();
    } catch (err) {
      console.error('❌ فشل تهيئة البوت بعد الاتصال:', err.message || err);
    }
  });

  client.on('reconnecting', () => console.warn('🔄 جارٍ إعادة الاتصال مع Discord...'));
  client.on('warn', (info) => console.warn('⚠️ تحذير Discord:', info));
  client.on('error', (err) => console.error('❌ خطأ في عميل Discord:', err.message || err));

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
      if (shouldIgnoreInteractionError(err)) {
        console.warn(`⚠️ تجاهل تفاعل منتهي/مكرر [${type}] [${id}]`);
        return;
      }
      console.error(`❌ خطأ [${type}] [${id}]:`, err.message || err);
      const msg = { content: '❌ حدث خطأ أثناء معالجة الطلب', flags: MessageFlags.Ephemeral };
      if (interaction.deferred || interaction.replied) {
        await interaction.followUp(msg).catch(() => {});
      } else {
        await interaction.reply(msg).catch(() => {});
      }
    }
  });

  client.login(token).catch((err) => {
    console.error('❌ فشل تسجيل الدخول:', err.message || err);
    process.exit(1);
  });

  return client;
}

async function registerCommands() {
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
      .setName('لوحة_التحكم')
      .setDescription('⚙️ نشر لوحة التحكم في الروم الحالي (للمسؤولين)'),
    new SlashCommandBuilder()
      .setName('إعدادات')
      .setDescription('⚙️ عرض أو تحديث إعدادات السيرفر')
      .addRoleOption(option => option.setName('رتبة_المسؤول').setDescription('رتبة المسؤولين').setRequired(false))
      .addRoleOption(option => option.setName('رتبة_المفعل').setDescription('رتبة المطلوبة للتقديم').setRequired(false))
      .addRoleOption(option => option.setName('رتبة_المقبولة').setDescription('رتبة تُمنح عند قبول الطلب').setRequired(false))
      .addChannelOption(option => option.setName('روم_الطلبات').setDescription('روم عرض الطلبات').setRequired(false))
      .addChannelOption(option => option.setName('روم_النموذج').setDescription('روم نشر نموذج التقديم').setRequired(false))
      .addChannelOption(option => option.setName('روم_السجلات').setDescription('روم إرسال السجلات').setRequired(false))
      .addChannelOption(option => option.setName('روم_التحكم').setDescription('روم لوحة التحكم').setRequired(false))
      .addBooleanOption(option => option.setName('فتح_التقديم').setDescription('فتح أو إغلاق التقديم').setRequired(false)),
  ];

  const rest = new REST({ version: '10' }).setToken(process.env.BOT_TOKEN);
  try {
    const guilds = await getGuilds();
    if (!guilds.length) {
      await rest.put(Routes.applicationCommands(client.user.id), { body: commands.map(c => c.toJSON()) });
      console.log('✅ تم تسجيل الأوامر عالمياً');
      return;
    }

    for (const guild of guilds) {
      await rest.put(Routes.applicationGuildCommands(client.user.id, guild.id), { body: commands.map(c => c.toJSON()) });
    }
    console.log('✅ تم تسجيل الأوامر على السيرفرات');
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
    const userApps = await db.applications.getByUser(interaction.user.id, interaction.guildId);
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

    const settings = await db.settings.get(interaction.guildId);
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
      components: [new ActionRowBuilder().addComponents(btn)],
      files: [{ attachment: LOCAL_IMAGES.form, name: 'emg3.png' }],
    });

    await interaction.editReply({ content: '✅ تم نشر النموذج في هذا الروم!' });
  } else if (interaction.commandName === 'لوحة_التحكم') {
    if (!(await canManageSettings(interaction))) {
      return interaction.reply({ content: '❌ هذا الأمر مخصص للمسؤولين فقط.', flags: MessageFlags.Ephemeral });
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });
    await postControlPanelToChannel(interaction.channel);
    await interaction.editReply({ content: '✅ تم نشر لوحة التحكم في هذا الروم!' });
  } else if (interaction.commandName === 'إعدادات') {
    if (!(await canManageSettings(interaction))) {
      return interaction.reply({ content: '❌ هذا الأمر مخصص للمسؤولين فقط.', flags: MessageFlags.Ephemeral });
    }

    const guildId = interaction.guildId;
    const settings = await db.settings.get(guildId);
    const hasUpdates = [
      'رتبة_المسؤول',
      'رتبة_المفعل',
      'رتبة_المقبولة',
      'روم_الطلبات',
      'روم_النموذج',
      'روم_السجلات',
      'روم_التحكم',
      'فتح_التقديم',
    ].some(name => interaction.options.get(name) !== null);

    if (!hasUpdates) {
      const embed = new EmbedBuilder()
        .setColor(0xd4af37)
        .setTitle('⚙️ إعدادات السيرفر')
        .addFields(
          { name: 'رتبة المسؤول', value: settings.admin_role_id ? `<@&${settings.admin_role_id}>` : 'لم تُضبط', inline: true },
          { name: 'رتبة المفعل', value: settings.activated_role_id ? `<@&${settings.activated_role_id}>` : 'لم تُضبط', inline: true },
          { name: 'رتبة المقبولة', value: settings.approved_role_id ? `<@&${settings.approved_role_id}>` : 'لم تُضبط', inline: true },
          { name: 'روم الطلبات', value: settings.requests_channel_id ? `<#${settings.requests_channel_id}>` : 'لم يُضبط', inline: true },
          { name: 'روم النموذج', value: settings.form_channel_id ? `<#${settings.form_channel_id}>` : 'لم يُضبط', inline: true },
          { name: 'روم السجلات', value: settings.logs_channel_id ? `<#${settings.logs_channel_id}>` : 'لم يُضبط', inline: true },
          { name: 'روم التحكم', value: settings.control_channel_id ? `<#${settings.control_channel_id}>` : 'لم يُضبط', inline: true },
          { name: 'فتح التقديم', value: settings.submissions_open ? 'مفتوح' : 'مغلق', inline: true },
        )
        .setFooter({ text: 'استخدم الأمر مرة أخرى مع الخيارات التي تريد تحديثها' })
        .setTimestamp();

      return interaction.reply({ embeds: [embed], flags: MessageFlags.Ephemeral });
    }

    const updates = [];
    const adminRole = interaction.options.getRole('رتبة_المسؤول');
    if (adminRole) {
      await db.settings.update(guildId, 'admin_role_id', adminRole.id);
      updates.push(`رتبة المسؤول: ${adminRole}`);
    }

    const activatedRole = interaction.options.getRole('رتبة_المفعل');
    if (activatedRole) {
      await db.settings.update(guildId, 'activated_role_id', activatedRole.id);
      updates.push(`رتبة المفعل: ${activatedRole}`);
    }

    const approvedRole = interaction.options.getRole('رتبة_المقبولة');
    if (approvedRole) {
      await db.settings.update(guildId, 'approved_role_id', approvedRole.id);
      updates.push(`رتبة المقبولة: ${approvedRole}`);
    }

    const requestsChannel = interaction.options.getChannel('روم_الطلبات');
    if (requestsChannel) {
      await db.settings.update(guildId, 'requests_channel_id', requestsChannel.id);
      updates.push(`روم الطلبات: ${requestsChannel}`);
    }

    const formChannel = interaction.options.getChannel('روم_النموذج');
    if (formChannel) {
      await db.settings.update(guildId, 'form_channel_id', formChannel.id);
      updates.push(`روم النموذج: ${formChannel}`);
    }

    const logsChannel = interaction.options.getChannel('روم_السجلات');
    if (logsChannel) {
      await db.settings.update(guildId, 'logs_channel_id', logsChannel.id);
      updates.push(`روم السجلات: ${logsChannel}`);
    }

    const controlChannel = interaction.options.getChannel('روم_التحكم');
    if (controlChannel) {
      await db.settings.update(guildId, 'control_channel_id', controlChannel.id);
      updates.push(`روم التحكم: ${controlChannel}`);
    }

    const submissionsOpen = interaction.options.getBoolean('فتح_التقديم');
    if (submissionsOpen !== null) {
      await db.settings.update(guildId, 'submissions_open', submissionsOpen);
      updates.push(`فتح التقديم: ${submissionsOpen ? 'مفتوح' : 'مغلق'}`);
    }

    await sendPersistentForm(guildId);
    await sendControlPanel(guildId);

    return interaction.reply({
      content: `✅ تم تحديث الإعدادات بنجاح:\n${updates.map(item => `• ${item}`).join('\n')}`,
      flags: MessageFlags.Ephemeral,
    });
  }
}

async function handleModalSubmit(interaction) {
  if (!interaction.inGuild() || !interaction.guild) {
    return interaction.reply({ content: '❌ هذه العملية تعمل فقط داخل السيرفر.', flags: MessageFlags.Ephemeral });
  }

  if (interaction.customId === 'application_form') {
    const full_name = interaction.fields.getTextInputValue('full_name');
    const age = interaction.fields.getTextInputValue('age');
    const reason = interaction.fields.getTextInputValue('reason');

    if (isNaN(age) || parseInt(age) < 16 || parseInt(age) > 150) {
      return interaction.reply({ content: '❌ العمر يجب أن يكون رقماً صحيحاً فوق 15 سنة', flags: MessageFlags.Ephemeral });
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const app = await db.applications.create({
      full_name,
      age: parseInt(age),
      reason,
      discord_user_id: interaction.user.id,
      discord_username: interaction.user.username,
      guild_id: interaction.guildId,
    });

    await db.logs.create({
      application_id: app.id,
      action: 'submit',
      performed_by: interaction.user.username,
      performed_by_id: interaction.user.id,
      details: `تقديم طلب جديد بواسطة ${full_name}`,
    });

    await interaction.editReply({ content: '✅ تم إرسال طلبك بنجاح! سيتم مراجعته من قبل المسؤولين.' });

    try {
      await sendApplicationToDiscord(app, interaction.guild);
    } catch (err) {
      console.error(`❌ فشل إرسال طلب ${app.id} إلى الروم:`, err);
    }

    return;
  }

  if (interaction.customId.startsWith('reject_reason_')) {
    const appId = interaction.customId.replace('reject_reason_', '');
    const reason = interaction.fields.getTextInputValue('rejection_reason');
    const app = await db.applications.getById(appId);

    if (!app) {
      return interaction.reply({ content: '❌ لم يتم العثور على الطلب.', flags: MessageFlags.Ephemeral });
    }

    if (app.status !== 'pending') {
      return interaction.reply({ content: '❌ تم معالجة هذا الطلب بالفعل.', flags: MessageFlags.Ephemeral });
    }

    const guild = interaction.guild;
    const settings = await db.settings.get(guild.id);
    const logsChannel = settings.logs_channel_id
      ? await resolveTextChannel(guild, settings.logs_channel_id, 'قناة السجلات')
      : null;

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    await db.applications.update(appId, {
      status: 'rejected',
      rejection_reason: reason,
      reviewed_by: interaction.user.tag,
      reviewed_by_id: interaction.user.id,
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
    });

    await db.logs.create({
      application_id: appId,
      action: 'reject',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم رفض طلب ${app.full_name} بواسطة ${interaction.user.tag} بسبب: ${reason}`,
    });

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
          `**👮 بواسطة:** <@${interaction.user.id}>\n` +
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
          .setImage('attachment://emg5.png')
          .setFooter({ text: 'وزارة الصحة' })
          .setTimestamp();
        await targetMember.send({
          embeds: [notifyEmbed],
          files: [{ attachment: LOCAL_IMAGES.rejected, name: 'emg5.png' }],
        }).catch(() => {});
      } catch (err) {
        console.error('خطأ في إرسال إشعار:', err);
      }
    }

    await removeApplicationMessageFromRequests(guild, appId);
    await interaction.editReply({ content: '❌ تم رفض الطلب.' });
  }
}

async function sendApplicationToDiscord(application, guild) {
  if (!client || !client.isReady()) {
    console.error('البوت غير جاهز لإرسال الطلب');
    return false;
  }

  if (!guild) {
    console.error('❌ لم أتمكن من الحصول على بيانات السيرفر لإرسال الطلب.');
    return false;
  }

  const settings = await db.settings.get(guild.id);
  if (!settings.requests_channel_id) {
    console.error('❌ لم يتم تعيين روم الطلبات في إعدادات السيرفر.');
    return false;
  }

  const channel = await resolveTextChannel(guild, settings.requests_channel_id, 'قناة الطلبات');
  if (!channel) {
    console.error(`❌ تعذّر الوصول إلى قناة الطلبات ${settings.requests_channel_id}.`);
    return false;
  }

  try {
    const user = await client.users.fetch(application.discord_user_id).catch(() => null);
    const safeReason = (application.reason || 'غير محدد').slice(0, 1024);

    const embed = new EmbedBuilder()
      .setColor(0x3498db)
      .setTitle('📋 طلب تقديم جديد')
      .setThumbnail(user?.displayAvatarURL() || 'https://cdn-icons-png.flaticon.com/512/3308/3308395.png')
      .addFields(
        { name: '👤 الاسم', value: application.full_name, inline: true },
        { name: '🎂 العمر', value: String(application.age), inline: true },
        { name: '📝 سبب التقديم', value: safeReason, inline: false },
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
    console.log(`تم إرسال الطلب ${application.id} بنجاح إلى الروم`);
    return true;
  } catch (err) {
    console.error(`❌ فشل إرسال الطلب ${application.id} إلى الروم:`, err);
    return false;
  }
}

async function removeApplicationMessageFromRequests(guild, appId) {
  if (!guild) {
    return;
  }

  const settings = await db.settings.get(guild.id);
  if (!settings.requests_channel_id) {
    return;
  }

  const channel = await resolveTextChannel(guild, settings.requests_channel_id, 'قناة الطلبات');
  if (!channel) {
    return;
  }

  try {
    const messages = await channel.messages.fetch({ limit: 50 });
    const target = messages.find(message => {
      const footer = message.embeds?.[0]?.footer?.text;
      return footer === `معرف الطلب: ${appId}`;
    });

    if (!target) {
      return;
    }

    await target.delete().catch(() => {});
  } catch (err) {
    console.error(`❌ فشل حذف رسالة الطلب ${appId} من روم الطلبات:`, err.message || err);
  }
}

async function sendPersistentForm(guildId = null) {
  if (!client || !client.isReady()) return;

  const guilds = guildId ? [await getGuildById(guildId)].filter(Boolean) : await getGuilds();

  for (const guild of guilds) {
    const settings = await db.settings.get(guild.id);
    if (!settings.form_channel_id) {
      continue;
    }

    const channel = await resolveTextChannel(guild, settings.form_channel_id, 'قناة النموذج');
    if (!channel) {
      continue;
    }

    const old = await findPersistentFormMessage(channel);
    const embed = new EmbedBuilder()
      .setColor(0xd4af37)
      .setTitle('📋 نموذج التقديم - وزارة الصحة')
      .setDescription(
        (settings.submissions_open
          ? 'اضغط على الزر أدناه لتقديم طلب جديد.'
          : 'التقديم حاليًا **مغلق** ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريباً إن شاء الله 🤲') +
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

    const editPayload = {
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)],
    };
    const sendPayload = {
      embeds: [embed],
      components: [new ActionRowBuilder().addComponents(btn)],
      files: [{ attachment: LOCAL_IMAGES.form, name: 'emg3.png' }],
    };

    if (old) {
      try {
        await old.edit(editPayload);
        continue;
      } catch (err) {
        console.error('❌ فشل تحديث رسالة النموذج، سأعيد نشرها:', err.message || err);
        try {
          await old.delete().catch(() => {});
        } catch {}
      }
    }

    await channel.send(sendPayload);
  }
}

async function sendControlPanel(guildId = null) {
  if (!client || !client.isReady()) return;

  const guilds = guildId ? [await getGuildById(guildId)].filter(Boolean) : await getGuilds();

  for (const guild of guilds) {
    const settings = await db.settings.get(guild.id);
    if (!settings.control_channel_id) {
      continue;
    }

    const channel = await resolveTextChannel(guild, settings.control_channel_id, 'قناة التحكم');
    if (!channel) {
      continue;
    }

    await postControlPanelToChannel(channel, settings);
  }
}

async function handleButtonInteraction(interaction) {
  const { customId, guild, member } = interaction;
  const settings = await db.settings.get(guild.id);

  if (customId === 'open_form') {
    if (!settings.submissions_open) {
      const embed = new EmbedBuilder()
        .setColor(0xdc3545)
        .setImage('attachment://emg1.png')
        .setFooter({ text: ' وزارة الصحة' })
        .setTimestamp();

      return interaction.reply({
        embeds: [embed],
        files: [{ attachment: LOCAL_IMAGES.closed, name: 'emg1.png' }],
        flags: MessageFlags.Ephemeral,
      });
    }

    if (settings.activated_role_id && !member.roles.cache.has(settings.activated_role_id)) {
      return interaction.reply({ content: '❌ يجب أن تمتلك رتبة **مفعل** لتتمكن من التقديم.', flags: MessageFlags.Ephemeral });
    }

    if (settings.approved_role_id && member.roles.cache.has(settings.approved_role_id)) {
      return interaction.reply({ content: '❌ لديك بالفعل رتبة **مقبول**، لا يمكنك التقديم مجدداً.', flags: MessageFlags.Ephemeral });
    }

    const userApps = await db.applications.getByUser(interaction.user.id, interaction.guildId);
    if (userApps.some(a => a.status === 'pending')) {
      return interaction.reply({ content: '❌ لديك طلب قيد المراجعة بالفعل.', flags: MessageFlags.Ephemeral });
    }

    const modal = new ModalBuilder()
      .setCustomId('application_form')
      .setTitle('📋 نموذج التقديم');

    const fullName = new TextInputBuilder()
      .setCustomId('full_name').setLabel('اسمك')
      .setStyle(TextInputStyle.Short).setPlaceholder('أدخل اسمك الكامل')
      .setMaxLength(100)
      .setRequired(true);

    const age = new TextInputBuilder()
      .setCustomId('age').setLabel('عمرك')
      .setStyle(TextInputStyle.Short).setPlaceholder('مثال: 25')
      .setMaxLength(3)
      .setRequired(true);

    const reason = new TextInputBuilder()
      .setCustomId('reason').setLabel('سبب التقديم')
      .setStyle(TextInputStyle.Paragraph).setPlaceholder('اكتب سبب تقديمك هنا...')
      .setMaxLength(1000)
      .setRequired(true);

    modal.addComponents(
      new ActionRowBuilder().addComponents(fullName),
      new ActionRowBuilder().addComponents(age),
      new ActionRowBuilder().addComponents(reason)
    );

    return interaction.showModal(modal);
  }

  if (customId === 'submissions_closed') {
    const CLOSED_IMAGE = 'attachment://emg1.png';
    const embed = new EmbedBuilder()
      .setColor(0xdc3545)
      .setImage(CLOSED_IMAGE)
      .setDescription('التقديم مغلق حالياً ✋\nيرجى الانتظار حتى يفتح التقديم المقبل قريباً إن شاء الله 🤲')
      .setFooter({ text: ' وزارة الصحة' })
      .setTimestamp();

    return interaction.reply({
      embeds: [embed],
      files: [{ attachment: LOCAL_IMAGES.closed, name: 'emg1.png' }],
      flags: MessageFlags.Ephemeral,
    });
  }

  if (customId === 'toggle_submissions') {
    if (!(await canManageSettings(interaction))) {
      return interaction.reply({ content: '❌ ليس لديك صلاحية للقيام بهذا الإجراء.', flags: MessageFlags.Ephemeral });
    }

    await interaction.deferReply({ flags: MessageFlags.Ephemeral });

    const newValue = !settings.submissions_open;
    await db.settings.update(guild.id, 'submissions_open', newValue);

    const toggleBtn = new ButtonBuilder()
      .setCustomId('toggle_submissions')
      .setLabel(newValue ? '🔒 إغلاق التقديم' : '✅ فتح التقديم')
      .setStyle(newValue ? ButtonStyle.Danger : ButtonStyle.Success);

    try {
      await interaction.message.edit({ components: [new ActionRowBuilder().addComponents(toggleBtn)] });
    } catch (err) {
      console.error('فشل تحديث الزر:', err);
    }

    await sendPersistentForm(guild.id);
    await sendControlPanel(guild.id);

    await interaction.editReply({ content: newValue ? '✅ تم فتح التقديم' : '🔒 تم إغلاق التقديم' });
    return;
  }

  if (!(await canManageSettings(interaction))) {
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
      reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString(),
    });

    await db.logs.create({
      application_id: appId,
      action: 'approve',
      performed_by: interaction.user.tag,
      performed_by_id: interaction.user.id,
      details: `تم قبول طلب ${app.full_name} بواسطة ${interaction.user.tag}`,
    });

    const logsChannel = settings.logs_channel_id
      ? await resolveTextChannel(guild, settings.logs_channel_id, 'قناة السجلات')
      : null;

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
          `**👮 بواسطة:** <@${interaction.user.id}>`
        )
        .setFooter({ text: ' وزارة الصحة' })
        .setTimestamp();
      await logsChannel.send({ embeds: [logEmbed] });
    }

    if (app.discord_user_id) {
      try {
        const targetMember = await guild.members.fetch(app.discord_user_id);
        const notifyEmbed = new EmbedBuilder()
          .setColor(0x28a745)
          .setImage('attachment://emg4.png')
          .setFooter({ text: ' وزارة الصحة' })
          .setTimestamp();
        await targetMember.send({
          embeds: [notifyEmbed],
          files: [{ attachment: LOCAL_IMAGES.approved, name: 'emg4.png' }],
        }).catch(() => {});

        if (settings.approved_role_id) {
          await targetMember.roles.add(settings.approved_role_id).catch(() => {});
        }
      } catch (err) {
        console.error('خطأ في إرسال إشعار أو إعطاء رتبة:', err);
      }
    }

    await removeApplicationMessageFromRequests(guild, appId);
    await interaction.editReply({ content: '✅ تم قبول الطلب بنجاح!' });

    return;
  }

  if (customId.startsWith('reject_')) {
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
