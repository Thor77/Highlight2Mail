import znc
import smtplib

class highlight2mail(znc.Module):
    description = 'Send highlights to a mail-adress while away'
    module_types = [znc.CModInfo.NetworkModule]

    #nick = znc.CZNC.Get().GetUser()

    def OnLoad(self, args, message):
        # constants
        self.PRIVMSG = '[{}] Private message from {}: {}'
        self.PRIVACTION = '[{}] Private action from {}: {}'
        self.PRIVNOTICE  = '[{}] Private notice from {}: {}'
        self.CHANMSG = '[{}] Message in {} from {}: {}'
        self.CHANACTION = '[{}] Action in {} from {}: {}'
        self.CHANNOTICE = '[{}] Notice in {} from {}: {}'

        self.vars = ['smtp_server', 'smtp_port', 'username', 'password', 'recipient', 'ssl']
        if 'catch_count' not in self.nv:
            self.nv['catch_count'] = '5'
        self.messages = []
        self.error = False
        self.network = self.GetNetwork()

        self.PutModule('You enabled me! You should set your mailserver-settings now!')
        self.help_command([])
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

    def catch_count_command(self, args):
        if len(args) >= 1 and args[0]:
            setting = str(args[0])
            self.nv['catch_count'] = setting
            self.PutModule('Set highlights until mail to {}'.format(setting))
        else:
            self.PutModule('Current highlights until mail: {}'.format(self.nv['catch_count']))
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
        self.PutModule('messages | show catched messages')
        self.PutModule('mailserver <var> <value> | set mailserver-<var> to <value>')
        self.PutModule('vars | display mailserver-vars')
        return True

    def set_command(self, args):
        if len(args) >= 2:
            var = str(args[0])
            value = str(args[1])
            if var in self.vars:
                self.nv[var] = value
                self.PutModule('Successfully set "{}" to "{}"!'.format(var, value))
            else:
                self.PutModule('ERROR! Invalid var! Try "vars" for a list of variables!')
        else:
            self.PutModule('ERROR! To less arguments! Try "help" for further information!')
        return True

    def vars_command(self, args):
        for k in self.vars:
            if k in self.nv:
                v = self.nv[k]
            else:
                v = None
            self.PutModule('{}  =  {}'.format(k, v))
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
            ssl = bool(self.nv['ssl'])
        except:
            self.error = 'Couldn\'t send mail! Mailserver-vars missing! Try "help" to get information how to fix it!'
            return            

        if ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)
            smtp.starttls()
        try:
            smtp.login(username, password)
        except smtplib.SMTPAuthenticationError:
            self.error = 'Couldn\'t send mail! Authentication failed!'
            return
        msg = 'Subject: Highlight2Mail\n\n{}'.format('\n'.join(messages))
        smtp.sendmail(username, recipient, msg)
        smtp.quit()
        # reset
        self.messages = []

    def catch(self, t, *args):
        args = [a for a in args]
        if len(args) >= 4:
            if self.network.GetNick() in args[3] and not self.network.IsUserAttached():
                self.messages.append(t.format(args[0], args[1], args[2], args[3]))
        else:
            if self.network.GetNick() in args[2] and not self.network.IsUserAttached():
                self.messages.append(t.format(args[0], args[1], args[2]))
        messages = self.messages
        if len(messages) >= int(self.nv['catch_count']) and not self.error:
            self.send_mail(messages)

    def OnClientLogin(self):
        if self.error:
            self.PutModule(self.error)
            self.messages_command([])
            self.error = False

    #
    # events
    #

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