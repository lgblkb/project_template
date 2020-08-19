import os
from secrets import choice
import string

password_length = 32
alphabet = string.ascii_letters + string.digits
password = ''.join(choice(alphabet) for i in range(password_length))

filename = './provision/.secret'
assert not os.path.exists(filename)
with open(filename, 'w') as file:
    file.write(password)
