//SPDX-License-Identifier: Unlicense
pragma solidity ^0.8.19;

import './Project.sol';

contract CrowdfundingPlatform {
    Project[] private projects; // TODO: remove?

    event ProjectCreated(address indexed _address);

    function createProject(string memory projectTitle) public {
        Project project = new Project(projectTitle);
        emit ProjectCreated(address(project));
    }

    function getAllProjects() external view returns (Project[] memory) {
        return projects;
    }
}

