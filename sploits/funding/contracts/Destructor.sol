// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

contract Destructor {
	constructor() payable {
	}

	function destruct(address addr) public {
		selfdestruct(payable(addr));
	}
}