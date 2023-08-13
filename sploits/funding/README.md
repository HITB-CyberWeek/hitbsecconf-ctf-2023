This folder contains the exploit for the `funding` service.

It uses blockchain, so configure it first:
1. Open `config.js`
2. Specify ethereum node address with enabled HTTP API
3. Specify the list of ethereum accounts which the checker can use. Only first account will be used
4. This account must have enough money to deploy contract and donate to them

To run exploit, install requirements first:
```shell
npm install
```

How to run exploit:
```shell
./funding.sploit.js <HOST> <FLAG-ID>
```
where `<FLAG-ID>` is flag id received by the checking system (which is equal to project's id)

For instance,
```shell
./funding.sploit.js funding.team23.ctf.hitb.org 173
```
