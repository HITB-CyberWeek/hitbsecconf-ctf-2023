require("@nomiclabs/hardhat-ethers");

module.exports = {
    solidity: "0.8.19",
    networks: {
        hitb: {
            url: `http://104.248.94.168:8545`, // TODO: Change URL
            chainId: 68664447
        }
    }
};
