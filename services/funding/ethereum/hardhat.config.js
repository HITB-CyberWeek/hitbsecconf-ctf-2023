require("@nomiclabs/hardhat-ethers");

module.exports = {
    solidity: "0.8.19",
    networks: {
        hitb: {
            url: `http://104.248.94.168:8545`, // TODO: Change URL
            chainId: 68664447,
            accounts: ["00142c3a2b06df0a48e63fe0dd6ee7bdf99ade9ab5569ee57f72feeb5abee335"] // TODO: change private key
        }
    }
};
