# Instructions for the Organizers' Side of the Funding Service

This document provides guidelines for setting up the jury-side infrastructure of the "funding" service.

The "funding" service runs on a private Ethereum network powered by [geth](https://geth.ethereum.org/docs/fundamentals/private-network).

You'll need two VMs for the Ethereum bootnode and HTTP API. While it's possible to deploy them on the same machine, it's strongly recommended to keep them separate. Both VMs should have [`geth` installed](https://geth.ethereum.org/docs/getting-started/installing-geth).

## The First Node: Bootstrap Node

1. Generate and save the password for the main account:

```
echo -n <RANDOMLY-GENERATED-PASSWORD> > main_account_password.txt
```

2. Create the main account:

```
geth account new --datadir data --password main_account_password.txt
```

The address of the generated account will be displayed. Let's assume it's `0xa323249f793ff1e65f58d1e42b9b7f383a328dc1`, which will be used in the next steps.

3. Generate the genesis block and save it to `genesis.json`:

```
{
  "config": {
    "chainId": 68664447,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "berlinBlock": 0,
    "clique": {
      "period": 1,
      "epoch": 30000
    }
  },
  "difficulty": "1",
  "gasLimit": "30000000",
  "extradata": "0x0000000000000000000000000000000000000000000000000000000000000000a323249f793ff1e65f58d1e42b9b7f383a328dc10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
  "alloc": {
    "a323249f793ff1e65f58d1e42b9b7f383a328dc1": { "balance": "10000000000000000000000000000" }
  }
}
```

Note that it has our address `a323249f793ff1e65f58d1e42b9b7f383a328dc1` in two different places. Read the [manual](https://geth.ethereum.org/docs/fundamentals/private-network) for description of other fields in the genesis block.

4. Initialize the Ethereum database:

```
geth init --datadir data genesis.json
```

5. Start the Ethereum node:

```
geth --datadir data --networkid 68664447 --nat extip:10.10.10.5 --netrestrict 10.0.0.0/8 --unlock 0xA323249F793ff1E65F58D1E42b9b7F383a328DC1 --mine --miner.etherbase 0xA323249F793ff1E65F58D1E42b9b7F383a328DC1 --password main_account_password.txt
```

Note that is has our address `0xA323249F793ff1E65F58D1E42b9b7F383a328DC1` presents in two different places. This command also has our internal address (`10.10.10.5`), change it if you need. It also restrict connections to the node for `10.0.0.0/8` network.

6. In another terminal, run:

```
geth attach --exec admin.nodeInfo.enr data/geth.ipc
```

This will display the **bootnode enode**, which is a connection string for other nodes.

## The Second Node

1. Copy `genesis.json` from the bootstrap node.

2. Initialize the Ethereum database:

```
geth init --datadir data genesis.json
```

3. Run the node with HTTP API:

```
geth --datadir data --networkid 68664447 --netrestrict 10.0.0.0/8 --syncmode "full" --bootnodes "enr:..." --http --http.addr 0.0.0.0 --http.vhosts="*" --http.api "admin,eth,net,web3,txpool,personal"
```

Replace `--bootnodes` with the value from the 6th step of the bootstrap node setup.

## Funding Service Accounts

Transfer funds to internal accounts:

```
> eth.sendTransaction({from: "0xA323249F793ff1E65F58D1E42b9b7F383a328DC1", to: "0x23B42ADe1d5EC963e4D6dA9022eE648639eE93F1", value: web3.toWei(1000000)})
> eth.sendTransaction({from: "0xA323249F793ff1E65F58D1E42b9b7F383a328DC1", to: "0x583D7efd10b585C2e15e8DdaC1d8F341dc97CF9E", value: web3.toWei(1000000)})
> eth.sendTransaction({from: "0xA323249F793ff1E65F58D1E42b9b7F383a328DC1", to: "0x746De882ce66a637cF7a55C75827d2eeE047c831", value: web3.toWei(10000000)})
```

Don't forget to change `0xA323249F793ff1E65F58D1E42b9b7F383a328DC1` to your main address.

Populate other accounts:

```
["0x48ca2FF45F96d69612Ade9AFDF528707d23c1eBa", "0xa40DcBA45427919D9302446bA34fBf3404BEB702", "0x099Eac5B089111020bF19251d714C7ab4Da633b1", "0xa808A4E6DF943d93208F599f62b5d1B4AFC1613c", "0x038f360023aa8A098316550200Bf79c2E600c1b8", ...].map(x => eth.sendTransaction({from: "0xA323249F793ff1E65F58D1E42b9b7F383a328DC1", to: x, value: web3.toWei(1000000)}));
```

As previously, don't forget to change `0xA323249F793ff1E65F58D1E42b9b7F383a328DC1` with your account.

## Deploy Crowdfunding Smart Contract

Navigate to `services/funding/ethereum`, put the private key into the config, and run:

```
npm run deploy
```

**The Ethereum network is deployed.**

Configs use `eth.ctf.hitb.org` as a domain name for the second done. Remember to update DNS names in configs if needed.

## Generating Accounts

To generate 500 accounts (which is needed for running checkers for 250 teams in parallel), I used the following commands:

```
go install github.com/ethereum/go-ethereum/cmd/ethkey@latest

echo HitbFundingCheckerWalletF431u9fh > password.txt
for i in `seq 1 500`; do geth account new --datadir data --password password.txt; done
for i in data/keystore/*; do ~/go/bin/ethkey inspect --private --passwordfile password.txt $i; done
```

## Running the Faucet

Faucet is the service for giving money to participants. 

It source codes is located in 'services/funding/faucet'. Copy the faucet source code to the VM with HTTP API and run `docker compose up -d`.