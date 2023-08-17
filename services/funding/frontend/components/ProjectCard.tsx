import { Project } from '@/redux/reducers'
import { Web3 } from 'web3'
import { useAppSelector } from "@/redux/store";
import { donate, withdraw, getReward as getReward, loadProject } from "@/redux/interactions";
import { toastError, toastSuccess } from "@/app/toasts";
import { useEffect, useState } from "react"

export default function ProjectCard(props: {project: Project}) {
    const donation = Web3.utils.toWei(0.0001, "ether");

    const web3 = useAppSelector(state => state.web3.connection);
    const userAddress = useAppSelector(state => state.web3.userAddress);
    const isAuthenticated = useAppSelector(state => state.user.isAuthenticated);

    let [project, setProject] = useState(props.project);
    let [reward, setReward] = useState("");

    useEffect(() => {
        setProject(props.project);
        setReward("");
    }, [props.project]);

    const donateClick = async () => {
        try {
            await donate(web3, userAddress, project.address!, donation);
            toastSuccess(<>Successfully donated to the project <b>{project.title}</b></>);

            setProject(await loadProject(project.id));
        } catch (e) {
            console.error(e);
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const withdrawClick = async () => {
        try {
            let actualProject = await loadProject(project.id);
            await withdraw(web3, userAddress, project.address!, actualProject.totalDonations!);
            toastSuccess(`Successfully withdrawn your money`);
            setProject(await loadProject(project.id));
        } catch (e) {
            console.error(e);
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const getRewardClick = async () => {
        try {
            const reward = await getReward(project.id);
            setReward(reward);
        } catch (e) {
            console.error(e);
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    if (project.error) {
        return <div className="p-4 mb-2 text-sm text-red-800 rounded-lg bg-red-50 dark:bg-gray-800 dark:text-red-400" role="alert">
            <span className="font-medium">Error for project {project.id}:</span> {project.error}
        </div>
    }

    return <div className="card relative overflow-hidden mb-2">        
        <h1 className="font-sans text-xl text-gray font-semibold mb-2">
            {project.title}
            {project.isFinished && <span className="bg-blue-100 text-blue-800 text-sm font-medium mr-2 ml-4 px-2.5 py-0.5 rounded dark:bg-blue-900 dark:text-blue-300">FINISHED</span>}
        </h1>
        <p className="text-md font-sans text-gray">
            Total donations: {Web3.utils.fromWei(project.totalDonations!, "ether")} ETH            
        </p>
        <p className="text-md font-sans text-gray">
            Owner: {project.owner}
        </p>
        <p className="text-md font-sans text-gray">Last baker: {project.lastBaker}</p>
        <div className="pt-4 space-x-4">
            {!project.isFinished &&
                <button onClick={donateClick} type="button" className="small-button inline-flex">
                    Donate 0.0001 ETH
                </button>
            }
            {project.owner == userAddress && Web3.utils.toBigInt(project.totalDonations) != Web3.utils.toBigInt(0) && !project.isFinished && <button className="small-button" onClick={withdrawClick}>Withdraw and Finish</button>}
            {project.isFinished && project.lastBaker == userAddress && isAuthenticated && <>
                <button className="small-button" onClick={getRewardClick}>🥳 Get Reward</button>
                {reward && <span className="text-green-500"><b>Your reward:</b> {reward}</span>}
            </>}
            {project.isFinished && project.lastBaker == userAddress && !isAuthenticated && <>
                <div className="flex items-center p-4 text-sm text-green-800 rounded-lg bg-green-50 dark:bg-gray-800 dark:text-green-400" role="alert">
                    <svg className="flex-shrink-0 inline w-4 h-4 mr-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 .5a9.5 9.5 0 1 0 9.5 9.5A9.51 9.51 0 0 0 10 .5ZM9.5 4a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3ZM12 15H8a1 1 0 0 1 0-2h1v-3H8a1 1 0 0 1 0-2h2a1 1 0 0 1 1 1v4h1a1 1 0 0 1 0 2Z"/>
                    </svg>
                    <div>
                        You're the last baker! Authenticate to receive your reward
                    </div>
                </div>
            </>}
        </div>
    </div>
}
