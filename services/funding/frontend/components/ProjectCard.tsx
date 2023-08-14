import { Project } from '@/redux/reducers'
import { Web3 } from 'web3'
import { useAppDispatch, useAppSelector } from "@/redux/store";
import { donate, loadProjects, withdraw, getAward, loadProject } from "@/redux/interactions";
import { toastError, toastSuccess } from "@/app/toasts";
import { useEffect, useState } from "react"
import projects from '../../backend/dist/backend/src/routes/projects/index';

export default function ProjectCard(props: {project: Project}) {
    const { project } = props;
    const donation = Web3.utils.toWei(0.0001, "ether");

    const web3 = useAppSelector(state => state.web3.connection);
    const userAddress = useAppSelector(state => state.web3.userAddress);

    let [ totalDonations, setTotalDonations ] = useState(project.totalDonations ? Web3.utils.toBigInt(project.totalDonations!) : 0, );
    let [ award, setAward ] = useState("");

    useEffect(() => {
        if (props.project.totalDonations)
            setTotalDonations(Web3.utils.toBigInt(props.project.totalDonations));
        setAward("");
    }, [props.project]);

    const dispatch = useAppDispatch();

    const donateClick = async () => {
        try {
            await donate(web3, userAddress, project.address!, donation);
            toastSuccess(`Successfully donated to the project ${project.title}`);

            setTotalDonations(Web3.utils.toBigInt(totalDonations) + Web3.utils.toBigInt(donation));
        } catch (e) {
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const withdrawClick = async () => {
        try {
            let updatedProject = await loadProject(project.id);
            await withdraw(web3, userAddress, project.address!, updatedProject.totalDonations!);
            toastSuccess(`Successfully withdrawn your money`);
            await loadProjects(dispatch); // TODO: update only current project?
        } catch (e) {
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const getAwardClick = async () => {
        try {
            const award = await getAward(project.id);
            setAward(award);
        } catch (e) {
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
            Total donations: {Web3.utils.fromWei(totalDonations, "ether")} ETH            
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
            {project.owner == userAddress && totalDonations > 0 && !project.isFinished && <button className="small-button" onClick={withdrawClick}>Withdraw and Finish</button>}
            {project.isFinished && project.lastBaker == userAddress && <>
                <button className="small-button" onClick={getAwardClick}>🥳 Get Award</button>
                {award && <span className="text-green-500"><b>Your award:</b> {award}</span>}
            </>}
        </div>
    </div>
}
