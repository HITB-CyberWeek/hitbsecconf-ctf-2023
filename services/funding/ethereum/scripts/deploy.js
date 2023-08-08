const hardhat = require("hardhat");

async function main() {
    const CrowdfundingPlatform = await hardhat.ethers.getContractFactory("CrowdfundingPlatform");
    const crowdfundingPlatform = await CrowdfundingPlatform.deploy();

    await crowdfundingPlatform.deployed();

    console.log("CrowdfundingPlatform is deployed to:", crowdfundingPlatform.address);
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
