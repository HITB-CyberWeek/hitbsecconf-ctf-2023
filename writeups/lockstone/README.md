# Lockstone

## Description

The service allows to register with passwords and flags. It was written in Node.js with Keystone web interface, which in turn utilizes the Next.js React Framework. Keystone uses GraphQL for communication between the frontend and the backend.

## Flags

The flag is the a user attribute. Users can access their own flags, but they cannot access others' flags.


## The Vulnerability

The GraphQL allows to make a conditional requests which is where the vulnerability lies. Even when the attribute is not accessible, conditions are evaluated -- alowing us to make several requests to reveal the flag contents.


## The Exploitation

For instance, we can ask if a user's first flag letter is 'A', then whether it's 'B', and so on.

Additionally, several several requests can be made in one query, enabling us to steal up to two letters per query.

```
query {
    i1_A:users(where:{id:{equals:"userid"},flag:{startsWith:"A"}}){id}
    i1_B:users(where:{id:{equals:"userid"},flag:{startsWith:"B"}}){id}
    ...
}
```

The full exsploit can be found at [/sploits/lockstone/spl.py](../../sploits/lockstone/spl.py).

A faster exploitation technique can be found in [/sploits/lockstone/spl_advanced.py](../../sploits/lockstone/spl_advanced.py). The concept is to use "less than" requests to determine the next letter. It divides the 0-9A-Z alphabet into four parts and determines the required part using three requests. Then, with 8 more requests it identifies the letter. When combined with retrieving several flags simultaneously, this method doubles the performance, allowing for speedy hacking.
