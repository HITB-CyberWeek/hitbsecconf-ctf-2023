This folder contains the checker for the `funding` service.

It uses blockchain, so configure it first:
1. Open `config.js`
2. Specify ethereum node address with enabled HTTP API
3. Specify the list of ethereum accounts which the checker can use. This list should contain at least two different accounts
4. These accounts must have enough money to deploy contracts and donate to them

To run checker, install requirements first:
```shell
npm install
```

If you change contract's ABI, copy it to the checker folder:
```
cp ../../services/funding/ethereum/artifacts/contracts/CrowdfundingPlatform.sol/CrowdfundingPlatform.json ../../services/funding/ethereum/artifacts/contracts/Project.sol/Project.json contracts/
```
