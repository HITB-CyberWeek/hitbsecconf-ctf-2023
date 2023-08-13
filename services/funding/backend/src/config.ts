import { configDotenv } from "dotenv";

configDotenv()

function loadEnvironmentVariable(variableName: string, defaultValue?: string): string {
    const envVar = process.env[variableName];

    if (!envVar) {
        if (defaultValue)
            return defaultValue;
        throw new Error(`You should specify $${variableName} via environment variable or .env file`)
    }

    return envVar;
}

export default {
    databaseUrl: loadEnvironmentVariable('DATABASE_URL'),
    ethereumNodeUrl: loadEnvironmentVariable('ETHEREUM_NODE_URL'),
    crowdfundingPlatformAddress: loadEnvironmentVariable('CROWDFUNDING_PLATFORM_ADDRESS'),
}
