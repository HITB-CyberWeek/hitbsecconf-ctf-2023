# Description
This service stores license keys. Your company comes here, entering some License key for service and gets token. Further they may use this token to get license key.
You may register or log in on site (login is a company name, it is a flag id).
After login you may leave some license key (it is a flag) and get token. Using this token any visitor may
get license key. You may find company by two or more symbols in name.

So you don't know the token for license key and can not get flag.



# Internals

The GetTOK function call in the "/make_license" path is the main secret of this service. It invokes an obfuscated function in the "token_generator.pyc" file, which is a compiled Python bytecode file. The obfuscation techniques used include:
   - Splitting basic blocks (linear sequences of commands) into smaller blocks
   - Shuffling the order of basic blocks
   - Packing strings

As a result, tools like decompyle3 or uncompyle cannot reverse-engineer this file. However, the original Python file, "token_generator.py", can be found.

The GetTOK function takes no arguments but accesses the company local variable from the caller function using the "inspect" module. It also takes the "User-Agent" header from the global variable of the request and the hostname of the computer. These three elements are concatenated into the "myCOMP1" variable. Then, a hash value (referred to as "hash1") is computed. Additionally, another hash value is computed using the secret key concatenated with "hash1" (secret key is a hardcoded string). The "hash1" and the sign are concatenated and returned as the token. The checker verifies the validity of the sign for "hash1". Therefore, it is not possible to simply return a random string instead of the token.

The token is saved to the database, and to obtain a license, you must send this token.
# Hacking

To create token you should know
    1. Company name. It is a flag id, you may find it via api or via "Search" button
    2. User-Agent. It is always "CTF" line
    3. Hostname. it is also always well-known
So if you found this then you may generate token without anything else.

## Way 1

You may reverse algorithm from pyc file and implement token generator in local computer.
But it is more simple to use the pyc file like a module. To do this you should have python3.8.

 1. To set any company name create local variable `company`
 2. To set any User-Agent create two classes like in next code
    
   ```ua = "CTF"
   class A2:
       def __init__(self):
           index=0
           self.data=['User-Agent']
       def get(self,a):
           global ua
           return ua
       def __iter__(self):
           self.index = 0
           return self
       def __next__(self):
           if self.index >= len(self.data):
               raise StopIteration
           result = self.data[self.index]
           self.index += 1
           return result
   class A1:
       def __init__(self):
           self.headers = A2()
   request=A1()
```
 3. To set hostname you should provide that `socket.gethostname()` return your value. So create file
 socket.py with next code
```
 def gethostname():
     return "team2-godeeper"
```
After that GetTOK() function will return a correct token

## Way 2
You may find that the hash function used in GetTOK is very weak. As a result, you can potentially attack the service like a black box.
Find a company name that is not equal to the flag ID and returns a correct token. For example, add an underscore "\_" symbol at the end of the flag ID. If you found a collision, you can register a company with a name like 'flagid\_\_\_\_\_\_\_' and obtain the correct token for a random license. After that, you can find the license associated with the flag using this token.


# Protection

To protect the service, you can:
1. Modify the company name (company local variable) before making the GetTOK call. This way, the token will not depend on the exact company name.
2. Modify the hostname on your machine.
3. Reverse the function GetTOK and observe that it sets the sign for the token. This sign is the only thing that is verified by the checker. Therefore, you can generate a token by combining a random string with the sign.
4. To protect from Way2 you may restrict length of company name
