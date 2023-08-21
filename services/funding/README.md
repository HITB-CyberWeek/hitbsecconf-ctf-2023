# Crowdfunding Platform

This directory contains the source code for the HITB Crowdfunding Platform, our innovative Web3 dApp.

The smart contract sources can be found in the `ethereum/contracts/` directory.

To deploy the contract onto the blockchain, follow these steps:

1. Navigate to the `ethereum/` directory: `cd ethereum`
2. Insert the private key of your Ethereum account into `hardhat.config.js` (if you're using MetaMask wallet, you can extract the private key from it; otherwise, you can create a separate account with a different tool)
3. Execute `npm run deploy`. If everything works find, this tool shows the address of the freshly deployed contract

If you've made changes to the contracts, remember to put this address of the Crowdfunding Platform Contract in `docker-compose.yml`, rebuild the images (`docker compose build`) and restart the service (`docker compose up -d`).

Note: Avoid altering the public interface (ABI) of contracts, as it can disrupt your service ;-)

If you wish to compile contracts using the Solidity Compiler without deploying them, use `npm run compile` instead of `npm run deploy`.
