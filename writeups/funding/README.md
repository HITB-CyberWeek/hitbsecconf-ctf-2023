# funding

## Overview

Crowdfunding is a Web3 decentralized application (dApp) that operates on a dedicated Ethereum network, eliminating the need for you to manage your own Ethereum node. The application allows users to register their Ethereum wallets and create crowdfunding projects using Smart Contracts. Contributors within the network can send funds to these projects.

## Usage

Upon creating a project, it is registered in the Ethereum network as a Smart Contract, enabling others to contribute funds. Project creators have the option to complete their project at any time and withdraw the collected funds. The last contributor to the project receives a customizable reward specified during project creation.

## Technical Aspects

The core of the service is the `Crowdfunding Platform` Smart Contract, located in the `ethereum/contracts/CrowdfundingPlatform.sol` file. This contract facilitates the creation of new projects through its `createProject()` method. 

	:::solidity
	function createProject(string memory projectTitle) public {
	    Project project = new Project(projectTitle);
	    emit ProjectCreated(address(project));
	}


This method instantiates a new Smart Contract, `Project`, based on the `ethereum/contracts/Project.sol` source file. This `Project` contract possesses crucial methods, including donation handling, project status checks, and fund withdrawal.

	:::solidity
	function donate() external payable {
	    require(msg.value >= 0.0001 ether, "Every donation should be at least 0.0001 ETH");
	    totalDonations = address(this).balance;
	    lastBaker = msg.sender;
	}

	function isFinished() public view returns (bool) {
	    return totalDonations != address(this).balance;
	}

	function withdraw(uint amount) external {
	    require(owner == payable(msg.sender), "Only owner can withdraw money");
	    require(amount <= address(this).balance, "You can not withdraw more than current balance");
	    require(amount > 0, "You can not withdraw 0 ether");

	    (bool success, ) = payable(owner).call{value: amount}("");
	    require(success, "Sorry, but I can not send money to you");
	}


## Vulnerability Overview

We can see that `totalDonations` field of the contract is changed when some user donates money to the project. In this case this field is setting to `address(this).balance`, and the project counts as non finished.

At the same time, if the owner calls `withdraw(amount)`, some money is payed to the owner, and `address(this).balance` changes. It marks the project as finished, and the person who was the last baker (`lastBaker`) receives the reward (which is the flag).

Unfortunately, for the projects with real flags nobody is going to "finish" them and withdraw the money. 

How we can "finish" it by ourselves? We should change `totalDonations` or `address(this).balance`, but not both of them. Changing `totalDonations` looks impossible, should we should try to change `address(this).balance`. We probably could send some money to the contract, but it doesn't have `fallback()`  or `receive()` [functions](https://coinsbench.com/solidity-17-payable-fallback-and-receive-d24b9f7d355f), so it looks like it doesn't accept money. 

Or not? In really, there is one more way to send money to the contract. Even if the contract doesn't want to accept that payment from you. It even can not reject this money! I'm talking about [`selfdestruct()`](https://www.metapunk.to/yongchanghe/tutorial-delete-a-contract-using-selfdestruct-34mi). This method allows to remove one contract and send all its money to the another address. It will increase the amount of destination, and this project will be counted as finished.

So, the solution is simple: we make the donation (to be the last baker), create a new smart contract `Destructor` by putting some money on it. This contract has only one method:

	:::solidity
	function destruct(address addr) public {
	    selfdestruct(payable(addr));
	}

Then we call this method with an address of the target project's contract, and grab our flag!

You can read more details about this technique with calling `selfdestruct` here: 

1. [Solidity by Example – Self-Destruct](https://solidity-by-example.org/hacks/self-destruct/)
2. [Hacker Noon – How to Hack Smart Contracts: Self-Destruct and Solidity](https://hackernoon.com/how-to-hack-smart-contracts-self-destruct-and-solidity)

The full exploit details can be found [here](../../sploits/funding/funding.sploit.js).
