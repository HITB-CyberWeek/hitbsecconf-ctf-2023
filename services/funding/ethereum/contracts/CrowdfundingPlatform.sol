//SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import './Project.sol';

contract CrowdfundingPlatform {
    event ProjectCreated(address indexed _address);

    function createProject(string memory projectTitle) public {
        Project project = new Project(projectTitle);
        emit ProjectCreated(address(project));
    }
}

