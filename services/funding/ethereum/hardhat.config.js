require("@nomiclabs/hardhat-ethers");

module.exports = {
    solidity: "0.8.19",
    networks: {
        hitb: {
            url: "http://eth.ctf.hitb.org:8545",
            chainId: 68664447,
            accounts: [
                // Insert your private key here
            ]
        }
    }
};
