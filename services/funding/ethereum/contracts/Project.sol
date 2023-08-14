//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Project {
    address payable private owner;
    uint256 private totalDonations;
    address private lastBaker;
    string private title;

    constructor(string memory _title) {
        owner = payable(tx.origin);
        totalDonations = address(this).balance;
        title = _title;
    }

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

    function getTotalDonations() external view returns (uint256) {
        return totalDonations;
    }

    function getLastBaker() external view returns (address) {
        return lastBaker;
    }

    function getOwner() external view returns (address) {
        return owner;
    }

    function getTitle() external view returns (string memory) {
        return title;
    }
}