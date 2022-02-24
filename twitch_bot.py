#!/usr/bin/env python3
import os # for importing env vars for the bot to use
import socket
import select
import time
from threading import Thread
import sqlite3
import tkinter as tk
import sys

class Command_DB():
    def __init__(self):
        pass
    def make_connection(self,DBname):
        try:
            conn = sqlite3.connect(DBname)
            errormsg=''
        except conn.Error as e:
            errormsg=e  
        return conn,errormsg
    
    def Get_tables(self,conn):
        cursor=conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables=[v[0] for v in cursor.fetchall() if v[0] != "sqlite_sequence"]
        return tables
    
    def create_DB(self,conn):
        tables=self.Get_tables(conn)
        if tables != ['Commands']:
            cursor=conn.cursor()
            sqlcmd="""CREATE TABLE Commands (
            Cmd_Name TEXT NOT NULL,
            Cmd_Text TEXT NOT NULL,
            Cmd_ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
            )"""
            cursor.execute(sqlcmd)
            conn.commit()
            
    def list_commands(self,conn):
        cursor=conn.cursor()
        sqlcmd='''SELECT Cmd_Name FROM Commands'''
        cursor.execute(sqlcmd)
        return cursor.fetchall()
    
    def check_if_command_exists(self,conn,cmd_to_check):
        cursor=conn.cursor()
        sqlcmd='''SELECT Cmd_Name FROM Commands WHERE Cmd_Name=?'''
        cursor.execute(sqlcmd,(cmd_to_check,))
        cmd=cursor.fetchall()
        if [(cmd_to_check,)] == cmd:
            errormsg="Command already exists."
        else:
            errormsg="Command doesn't exist."
        return errormsg
    
    def get_command(self,conn,cmd_to_get):
        errormsg=self.check_if_command_exists(conn,cmd_to_get)
        if errormsg=="Command doesn't exist.":
            return errormsg
        else:
            cursor=conn.cursor()
            sqlcmd = ''' SELECT Cmd_Text from Commands WHERE Cmd_Name=? ''' 
            cursor.execute(sqlcmd,(cmd_to_get,))
            [(cmdtext,)]=cursor.fetchall()
            return cmdtext
            
    
    def insert_into_commands(self,conn,cmd_to_insert):
        errormsg=self.check_if_command_exists(conn,cmd_to_insert[0])
        if errormsg=="Command doesn't exist.":
            cursor=conn.cursor()
            sqlcmd = ''' INSERT INTO Commands (Cmd_Name,Cmd_Text) 
        VALUES(?,?) '''
            cursor.execute(sqlcmd,cmd_to_insert)
            conn.commit()
            return "Command added successfully."
        else:
            return errormsg
    
    def delete_command(self,conn, Cmd_Name):
        errormsg=self.check_if_command_exists(conn,Cmd_Name)
        if errormsg == "Command already exists.":    
            cursor = conn.cursor()
            sqlcmd = ''' DELETE FROM Commands WHERE Cmd_Name=? '''
            cursor.execute(sqlcmd, (Cmd_Name,))
            conn.commit()
            return 'Command successfully deleted.'
        else:
            return errormsg

class User_DB():
    def __init__(self):
        pass
    def make_connection(self,DBname):
        try:
            conn = sqlite3.connect(DBname)
            errormsg=''
        except conn.Error as e:
            errormsg=e  
        return conn,errormsg
    
    def create_DB(self,conn):
        cursor=conn.cursor()
        sqlcmd="""CREATE TABLE Users (
        User TEXT NOT NULL,
        User_ID INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT
        )"""
        cursor.execute(sqlcmd)
        conn.commit()
    
    def check_if_user_exists(self,conn,user_to_check):
        cursor=conn.cursor()
        sqlcmd='''SELECT User FROM Users WHERE User=?'''
        cursor.execute(sqlcmd,(user_to_check,))
        user=cursor.fetchall()
        if [(user_to_check,)] == user:
            errormsg="User already exists."
        else:
            errormsg='User added successfully.'
        return errormsg
    
    def insert_into_users(self,conn,user_to_insert):
        errormsg=self.check_if_user_exists(conn,user_to_insert[0])
        if errormsg=='User added successfully.':
            cursor=conn.cursor()
            sqlcmd = ''' INSERT INTO Users (User) VALUES(?) '''
            cursor.execute(sqlcmd,user_to_insert)
            conn.commit()
        return errormsg

class MyBot():
    
    def __init__(self):
        self.admins=[]
        self.automsg=[]
        with open(os.path.join(os.path.dirname(__file__),'credentials.txt'), 'r') as f:
            for line in f:
                a=line.strip()
                tmp=a.split('=')
                if tmp[0]=='token':
                    self.token=tmp[-1]
                if tmp[0]=='client':
                    self.client_id=tmp[-1]
                if tmp[0]=='nickname':
                    self.nickname=tmp[-1]
                if tmp[0]=='port':
                    self.port = int(tmp[-1])
                if tmp[0]=='server':
                    self.server=tmp[-1]
                if tmp[0]=='channel':
                    self.channel=tmp[-1]
                if tmp[0]=='admins':
                    self.admins.append(tmp[-1])
                if tmp[0]=='msg':
                    self.automsg.append(tmp[-1])
                if tmp[0]=='cookie':
                    self.emotikon = tmp[-1]
                if tmp[0]=='timeout':
                    self.timeout = int(tmp[-1])
                if tmp[0]=='timer':
                    self.repeat = int(tmp[-1])
        self.sock=socket.socket()
        self.sock.connect((self.server, self.port))
        self.T1 = Thread(target=self.check_incoming, args=())
        self.T2 = Thread(target=self.auto_send, args=())
        self.T1.daemon = True
        self.T2.daemon = True
        
    
    def check_incoming(self):
        #access to databases should be in this thread
        self.cmdconn,self.cmderror=Command_DB().make_connection(os.path.join(os.path.dirname(__file__),'Command.db'))
        Command_DB().create_DB(self.cmdconn)
        self.userconn,self.usererror=User_DB().make_connection(':memory:')
        User_DB().create_DB(self.userconn)
        while True:
            self.rwe = select.select([self.sock], [self.sock], [], self.timeout)
            if self.sock in self.rwe[0]:
                resp = self.sock.recv(2048).decode('utf-8')
                self.test_resp(resp)
            time.sleep(1) #putting thread to sleep

            
    def auto_send(self):
        while True:
            for automsg in self.automsg:
                self.rwe = select.select([self.sock], [self.sock], [], self.timeout)
                if self.sock in self.rwe[1]:
                    time.sleep(self.repeat)
                    self.sock.send(f"PRIVMSG {self.channel} : {automsg}\n".encode('utf-8'))
                    
                    
    
    def test_resp(self,resp):
        #can be optimized
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
        elif 'PRIVMSG' in resp:
            tmp=resp.strip().split(':')
            user=tmp[1].split('!')[0]#this gets the user
            tmp=resp.strip().split(' :')#this is needed if you add link to commands
            if tmp[-1].startswith('!'):
                if tmp[-1]=='!commands':
                    listcmd=Command_DB().list_commands(self.cmdconn)
                    if listcmd==[]:
                        self.sock.send(f"PRIVMSG {self.channel} : {'Currently there are no commands available.'}\n".encode('utf-8'))
                    else:
                        message='Available commands are:'
                        for item in listcmd:    
                            message=message+' '+item[0]
                        self.sock.send(f"PRIVMSG {self.channel} : {message}\n".encode('utf-8'))  
                elif tmp[-1].startswith('!add') and user in self.admins:
                    cmd=tmp[-1].split()
                    if len(cmd)<3 or not cmd[1].startswith('!'):
                        #should be checked
                        self.sock.send(f"PRIVMSG {self.channel} : {'Correct usage is: !add !command_name command_text'}\n".encode('utf-8'))
                    else:
                        command=cmd[2]
                        for word in cmd[3:]:
                            command=command+' '+word
                        error=Command_DB().insert_into_commands(self.cmdconn,(cmd[1],command))
                        self.sock.send(f"PRIVMSG {self.channel} : {error}\n".encode('utf-8'))
                elif tmp[-1].startswith('!del') and user in self.admins:
                    cmd=tmp[-1].split()
                    if len(cmd)!=2 or not cmd[1].startswith('!'):
                        self.sock.send(f"PRIVMSG {self.channel} : {'Correct usage is: !del !command_name'}\n".encode('utf-8'))
                    else:
                        error=Command_DB().delete_command(self.cmdconn,cmd[1])
                        self.sock.send(f"PRIVMSG {self.channel} : {error}\n".encode('utf-8'))
                elif tmp[-1].startswith('!add') and user not in self.admins:
                    self.sock.send(f"PRIVMSG {self.channel} : {'You are not allowed to do that!'}\n".encode('utf-8'))
                elif tmp[-1].startswith('!del') and user not in self.admins:
                    self.sock.send(f"PRIVMSG {self.channel} : {'You are not allowed to do that!'}\n".encode('utf-8'))
                else:
                    cmdtext=Command_DB().get_command(self.cmdconn,tmp[-1])
                    self.sock.send(f"PRIVMSG {self.channel} : {cmdtext}\n".encode('utf-8'))
                
            else:
                error=User_DB().insert_into_users(self.userconn,(user,))
                if error=='User added successfully.':
                    msg=self.emotikon+user
                    self.sock.send(f"PRIVMSG {self.channel} : {msg}\n".encode('utf-8'))
            
    def start_bot(self):
        self.sock.send(f"PASS {self.token}\r\n".encode('utf-8'))
        self.sock.send(f"NICK {self.nickname}\r\n".encode('utf-8'))
        self.sock.send(f"JOIN {self.channel}\r\n".encode('utf-8'))
        self.sock.send(f"PRIVMSG {self.channel} : {'Bot is now online!'}\n".encode('utf-8'))
        self.T1.start()
        self.T2.start()
    
    def stop_bot(self):
        self.sock.send(f"PRIVMSG {self.channel} : {'Bot has gone offline!'}\n".encode('utf-8'))
        self.sock.send(f"QUIT\n".encode('utf-8'))
        
   
class BotStuff():
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("300x150")
        self.root.title("App for starting TwitchBot!")
        self.chatBot=MyBot()
        self.init_mainframe()
        self.init_buttons()
        
    def init_mainframe(self):
        self.mainframe = tk.Frame(self.root)
        self.mainframe.grid(column=0,row=0)
        self.mainframe.columnconfigure(0, weight = 1)
        self.mainframe.rowconfigure(0, weight = 1)
        self.mainframe.pack(pady = 50, padx = 50)

    def init_start(self):
        self.root.mainloop()   
        
    def init_buttons(self): 
        self.startbttn=tk.Button(self.mainframe, text="Start Bot", command=self.Start)
        self.startbttn.grid(row=2,column=1)
        tk.Button(self.mainframe, text="Stop Bot", command=self.Close).grid(row=2,column=3)
        
    def Start(self):
        self.chatBot.start_bot()
        self.startbttn.configure(state='disabled')
        
    def Close(self):
        self.chatBot.stop_bot()
        self.root.destroy()
        sys.exit()
        
        
if __name__=='__main__':
    BotStuff.init_start(BotStuff())
