import znc
import smtplib

class highlight2mail(znc.Module):
    description = 'Send highlights to a mail-adress while away'
    module_types = [znc.CModInfo.NetworkModule]
    has_args = True
    args_help_text = 'Recipient-address'

    def OnLoad(self, args, message):
        # constants
        self.PRIVMSG = '[{}] Private message from {}: {}'
        self.PRIVACTION = '[{}] Private action from {}: {}'
        self.PRIVNOTICE  = '[{}] Private notice from {}: {}'
        self.CHANMSG = '[{}] Message in {} from {}: {}'
        self.CHANACTION = '[{}] Action in {} from {}: {}'
        self.CHANNOTICE = '[{}] Notice in {} from {}: {}'

        # set default vars
        self.defaults = {'smtp_server': 'localhost', 'smtp_port': '25', 'username': '', 'password': '', 'recipient': args}
        if 'smtp_server' not in self.nv:
            self.nv['smtp_server'] = 'localhost'
        if 'smtp_port' not in self.nv:
            self.nv['smtp_port'] = '25'
        if 'username' not in self.nv:
            self.nv['username'] = ''
        if 'password' not in self.nv:
            self.nv['password'] = ''

        if 'catch_count' not in self.nv:
            self.nv['catch_count'] = '5'
        if 'window_size' not in self.nv:
            self.nv['window_size'] = '10'
        self.messages = []
        self.window = []
        self.error = False
        self.network = self.GetNetwork()

        self.PutModule('You enabled me! You should set your mailserver-settings now (try "help")!')
        if args:
            self.nv['recipient'] = args
            self.PutModule('Set recipient to {}!'.format(args))
        else:
            self.nv['recipient'] = ''
        return True

    #
    # commands
    # doesn't work with python-bindings
    # https://github.com/znc/znc/issues/198

    # commands workarround
    def OnModCommand(self, cmd):
        split = cmd.split()
        c = str(split[0]).lower()
        args = [a.lower() for a in split[1:]]
        if c == 'help':
            self.help_command(args)
        elif c == 'catchcount':
            self.catch_count_command(args)
        elif c == 'set':
            self.set_command(args)
        elif c == 'vars':
            self.vars_command(args)
        elif c == 'messages':
            self.messages_command(args)
        elif c == 'windowsize':
            self.window_size_command(args)

    def catch_count_command(self, args):
        if len(args) >= 1 and args[0]:
            try:
                a = int(args[0])
            except:
                self.PutModule('Invalid catch count! Must be integer!')
                return True
            setting = str(args[0])
            self.nv['catch_count'] = setting
            self.PutModule('Set highlights until mail to {}'.format(setting))
        else:
            self.PutModule('Current highlights until mail: {}'.format(self.nv['catch_count']))
        return True

    def window_size_command(self, args):
        if len(args) >= 1 and args[0]:
            try:
                a = int(args[0])
            except:
                self.PutModule('Invalid window size! Must be integer!')
                return True
            setting = str(args[0])
            self.nv['window_size'] = setting
            self.PutModule('Set window size to {}'.format(setting))
        else:
            self.PutModule('Current window size: {}'.format(self.nv['window_size']))
        return True

    def messages_command(self, args):
        self.PutModule('Catched messages:')
        for message in self.messages:
            self.PutModule(message)
        self.PutModule('Messages until mail: {}'.format(int(self.nv['catch_count']) - len(self.messages)))
        self.messages = []
        self.PutModule('Successfully cleared messages!')

    def help_command(self, args):
        self.PutModule('catchCount [<highlights until mail>] | set the count of highlights until mail')
        self.PutModule('windowsize [<message window>] | set amount of messages to send with highlights')
        self.PutModule('messages | show catched messages')
        self.PutModule('mailserver <var> <value> | set mailserver-<var> to <value>')
        self.PutModule('vars | display mailserver-vars')
        return True

    def set_command(self, args):
        if len(args) >= 2:
            var = str(args[0])
            value = str(args[1])
            if var in self.nv:
                if value == 'default':
                    value = self.defaults[var]
                self.nv[var] = value
                self.PutModule('Successfully set "{}" to "{}"!'.format(var, value))
            else:
                self.PutModule('ERROR! Invalid var! Try "vars" for a list of variables!')
        else:
            self.PutModule('ERROR! To less arguments! Try "help" for further information!')
        return True

    def vars_command(self, args):
        for k in self.defaults:
            self.PutModule('{} = {}'.format(k, self.nv[k]))
        return True
    #
    #
    #

    def send_mail(self, messages):
        # send mail
        try:
            server = self.nv['smtp_server']
            port = int(self.nv['smtp_port'])
            username = self.nv['username']
            password = self.nv['password']
            recipient = self.nv['recipient']
            if not recipient:
                raise Exception()
        except:
            self.error = 'Some mail-vars have invalid values or are unset!'
            return

        smtp = smtplib.SMTP(server, port)
        smtp.starttls()

        try:
            if username and password:
                smtp.login(username, password)
        except smtplib.SMTPAuthenticationError:
            self.error = 'Couldn\'t send mail! Authentication failed!'
            return

        msg = 'Subject: Highlight2Mail\n\n'
        for window in self.messages:
            msg += '----'
            msg += '\n'.join(window)
            msg += '----'

        if not username:
            username = 'znc@znc.in'
        try:
            smtp.sendmail(username, recipient, msg)
        except Exception as e:
            self.error = '{}: {}'.format(e.__class__.__name__, e.args[0])
            return

        smtp.quit()
        # reset
        self.messages = []

    def add_message(self, msg, highlight):
        while len(self.window) >= (int(self.nv['window_size']) - 1):
            self.window.pop(0)
        self.window.append(msg)
        if highlight:
            self.messages.append(self.window)

    def catch(self, t, *args):
        args = [a for a in args]
        if not self.network.IsUserAttached():
            if len(args) >= 4:
                msg = t.format(args[0], args[1], args[2], args[3])
                highlight = (self.network.GetNick() in args[3])
            else:
                msg = t.format(args[0], args[1], args[2])
                highlight = (self.network.GetNick() in args[2])
            self.add_message(msg, highlight)
            messages = self.messages
            if len(messages) >= int(self.nv['catch_count']) and not self.error:
                self.send_mail(messages)


    #
    # events
    #

    def OnClientLogin(self):
        if self.error:
            self.PutModule(self.error)
            self.messages_command([])
            self.error = False

    def OnPrivMsg(self, nick, message):
        self.catch(self.PRIVMSG, self.GetNetwork().GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE

    def OnPrivAction(self, nick, message):
        self.catch(self.PRIVACTION, self.GetNetwork().GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE

    def OnPrivNotice(self, nick, message):
        self.catch(self.PRIVNOTICE, self.GetNetwork().GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE

    def OnChanMsg(self, nick, channel, message):
        self.catch(self.CHANMSG, self.GetNetwork().GetName(), channel.GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE

    def OnChanAction(self, nick, channel, message):
        self.catch(self.CHANACTION, self.GetNetwork().GetName(), channel.GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE

    def OnChanNotice(self, nick, channel, message):
        self.catch(self.CHANNOTICE, self.GetNetwork().GetName(), channel.GetName(), nick.GetNick(), str(message))
        return znc.CONTINUE