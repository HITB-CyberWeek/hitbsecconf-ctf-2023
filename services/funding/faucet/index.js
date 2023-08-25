const fastify = require('fastify')({logger: true})
const path = require('path')
const forwarded = require('@fastify/forwarded')
const Web3 = require('web3').Web3;
const connect = require('@databases/sqlite');
const {sql} = require('@databases/sqlite');
const config = require("./config.js");

const web3 = new Web3(config.ethereumNode);

const db = connect("database/db.sqlite");

db.query(sql`CREATE TABLE IF NOT EXISTS usage (id INTEGER PRIMARY KEY, network VARCHAR(50), timestamp INTEGER, amount REAL, transactionHash VARCHAR(100))`);

async function getUsage(transaction, network) {
    const result = await transaction.query(sql`SELECT SUM(amount) AS total FROM usage WHERE network=${network} AND datetime(timestamp) >= datetime('now', '-1 Hour')`);
    return result[0].total;
}

async function addUsage(transaction, network, amount, transactionHash) {
    await transaction.query(sql`INSERT INTO usage (network, timestamp, amount, transactionHash) VALUES (${network}, CURRENT_TIMESTAMP, ${amount}, ${transactionHash})`);
}

fastify.register(require('@fastify/static'), {
    root: path.join(__dirname, 'public'),
})

fastify.post('/request', async function (req, reply) {
    console.log(`Received request: ${JSON.stringify(req.body)}`);

    const userAddress = req.body["address"];
    const amount = parseFloat(req.body["amount"]);
    if (!userAddress || !amount) {
        console.error("Invalid request: there is no 'address' or 'amount' field");
        reply.send({status: "error", message: "Address or amount is empty"})
        return;
    }

    if (!userAddress.startsWith("0x")) {
        reply.send({status: "error", message: "Address should start with 0x..."})
        return;
    }

    if (amount < 1 || amount > 100) {
        reply.send({status: "error", message: "You can request amount between 1 and 100 ETH"});
        return;
    }

    const addresses = forwarded(req);
    if (!addresses) {
        console.error("Can not determine address from X-Forwarded-For header and TCP source address");
        reply.send({status: "error", message: "Can not determine your IP address"})
        return;
    }

    const originalAddress = addresses[addresses.length - 1];
    console.log(`List of IP addresses for the request: ${addresses}, we will use last of them: ${originalAddress}`);

    const ipAddressParts = originalAddress.split(".");
    if (parseInt(ipAddressParts[3]) < 20) {
        reply.send({status: "error", message: "It's prohibited to use this faucet from the service instance. Use your own laptop"});
        return;
    }
    const network = `${ipAddressParts[0]}.${ipAddressParts[1]}.${ipAddressParts[2]}.0/24`;

    await db.tx(async (dbTx) => {
        let currentUsage = await getUsage(dbTx, network) || 0;
        console.log(`Current usage for the network ${network} is ${currentUsage.toFixed(3)}, requested ${amount} ETH`);
        if (currentUsage + amount > config.limitPerNetworkPerHour) {
            reply.send({status: "error", message: `Your usage for the last hour is ${currentUsage.toFixed(3)}. You can not request ${amount} ETH now. Please wait.`})
            return;
        }

        const nonce = await web3.eth.getTransactionCount(config.address, "pending");
        const transaction = {from: config.address, to: userAddress, value: web3.utils.toWei(amount, "ether"), nonce};
        const estimateGas = await web3.eth.estimateGas(transaction);
        const gasPrice = await web3.eth.getGasPrice();
        const signedTransaction = await web3.eth.accounts.signTransaction({...transaction, gas: estimateGas, gasPrice}, config.privateKey);
        const receipt = await web3.eth.sendSignedTransaction(signedTransaction.rawTransaction)

        console.log(`Sent in the transaction ${receipt.transactionHash}`);

        await addUsage(dbTx, network, amount, receipt.transactionHash);
        await reply.send({status: "ok", blockNumber: receipt.blockNumber.toString(), transactionHash: receipt.transactionHash});
    });
})

fastify.listen({ port: 3000, host: process.env.FASTIFY_LISTEN || '127.0.0.1' }).catch(console.error);
