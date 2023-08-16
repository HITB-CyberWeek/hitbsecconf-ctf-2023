# Contracts

This folder contains Ethereum contracts for HITB Crowdfunding Platform. Contract sources are located in `contracts/` folder.

To deploy contract into blockhain, follow steps:

1. Insert the private key of your Ethereum account into `hardhat.config.js` (if you have MetaMask wallet you can extract the private key from it, otherwise you can create a separate account with any other tool)
2. Run `npm run deploy`

This command creates files in `artifacts/contracts/` folder which will be used by backend and frontend.

If you changed contracts, don't forget to put the address of Crowdfunding Platform in `docker-compose.yml` and restart the service.

Note: you don't want to change ABI of contracts, because you can break your service ;-)

If you want compile contracts by Solidity Compiler, but not deploy them, use:

`npm run compile`
