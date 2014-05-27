#!/usr/bin/python

from __future__ import print_function

import paramiko
import sys
import os
import subprocess
import select
import socket
import termios
import tty


def open_shell(connection, remote_name='SSH server'):
    """
    Opens a PTY on a remote server, and allows interactive commands to be run.
    Reassigns stdin to the PTY so that it functions like a full shell, as would
    be given by the OpenSSH client.

    Differences between the behavior of OpenSSH and the existing Paramiko
    connection can cause mysterious errors, especially with respect to
    authentication. By keeping the entire SSH2 connection within Paramiko, such
    inconsistencies are eliminated.

    Args:
        @connection
        A live paramiko SSH connection to the remote host.

    KWArgs:
        @remote_name="SSH server"
        The name to use to refer to the remote host during the connection
        closed message. Typically a valid FQDN or IP addr.
    """

    # get the current TTY attributes to reapply after
    # the remote shell is closed
    oldtty_attrs = termios.tcgetattr(sys.stdin)

    # invoke_shell with default options is vt100 compatible
    # which is exactly what you want for an OpenSSH imitation
    channel = connection.invoke_shell()

    def resize_pty():
        # resize to match terminal size
        tty_height, tty_width = \
                subprocess.check_output(['stty', 'size']).split()

        # try to resize, and catch it if we fail due to a closed connection
        try:
            channel.resize_pty(width=int(tty_width), height=int(tty_height))
        except paramiko.ssh_exception.SSHException:
            pass

    # wrap the whole thing in a try/finally construct to ensure
    # that exiting code for TTY handling runs
    try:
        stdin_fileno = sys.stdin.fileno()
        tty.setraw(stdin_fileno)
        tty.setcbreak(stdin_fileno)

        channel.settimeout(0.0)

        is_alive = True

        while is_alive:
            # resize on every iteration of the main loop
            resize_pty()

            # use a unix select call to wait until the remote shell
            # and stdin are ready for reading
            # this is the block until data is ready
            read_ready, write_ready, exception_list = \
                    select.select([channel, sys.stdin], [], [])

            # if the channel is one of the ready objects, print
            # it out 1024 chars at a time
            if channel in read_ready:
                # try to do a read from the remote end and print to screen
                try:
                    out = channel.recv(1024)

                    # remote close
                    if len(out) == 0:
                        is_alive = False
                    else:
                        # rely on 'print' to correctly handle encoding
                        print(out, end='')
                        sys.stdout.flush()

                # do nothing on a timeout, as this is an ordinary condition
                except socket.timeout:
                    pass

            # if stdin is ready for reading
            if sys.stdin in read_ready and is_alive:
                # send a single character out at a time
                # this is typically human input, so sending it one character at
                # a time is the only correct action we can take

                # use an os.read to prevent nasty buffering problem with shell
                # history
                char = os.read(stdin_fileno, 1)

                # if this side of the connection closes, shut down gracefully
                if len(char) == 0:
                    is_alive = False
                else:
                    channel.send(char)

        # close down the channel for send/recv
        # this is an explicit call most likely redundant with the operations
        # that caused an exit from the REPL, but unusual exit conditions can
        # cause this to be reached uncalled
        channel.shutdown(2)

    # regardless of errors, restore the TTY to working order
    # upon exit and print that connection is closed
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, oldtty_attrs)
        print('Paramiko channel to %s closed.' % remote_name)
