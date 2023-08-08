import { Project } from '@/redux/reducers'
import { Web3 } from 'web3'
import {useAppDispatch, useAppSelector} from "@/redux/store";
import {donate, loadProjects, withdraw} from "@/redux/interactions";
import {toastError, toastSuccess} from "@/app/toasts";

export default function ProjectCard(props: {project: Project}) {
    const { project } = props;
    const donation = Web3.utils.toWei(0.05, 'ether');

    const web3 = useAppSelector(state => state.web3.connection);
    const userAddress = useAppSelector(state => state.web3.userAddress);

    const dispatch = useAppDispatch();

    const donateClick = async () => {
        try {
            await donate(web3, userAddress, project.address!, donation);
            toastSuccess(`Successfully donated to the project ${project.title}`);

            totalDonations = Web3.utils.toWei(Web3.utils.fromWei(totalDonations, "ether") + 0.05, "ether");
        } catch (e) {
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const withdrawClick = async () => {
        try {
            await withdraw(web3, userAddress, project.address!, project.totalDonations!);
            toastSuccess(`Successfully withdrawn your money`);
            await loadProjects(dispatch); // TODO: update only current project?
        } catch (e) {
            toastError(e instanceof Error ? e.message : e as string);
        }
    }

    const getAwardClick = async () => {

    }

    if (project.error) {
        return <div>{project.error}</div>;
    }

    let totalDonations = project.totalDonations!;

    return <div className="card relative overflow-hidden my-4">
        {/*<div className={`ribbon ${colorMaker(props.state)}`}>{props.state}</div>*/}
        <h1 className="font-sans text-xl text-gray font-semibold">{project.title}</h1>
        <p className="text-md font-sans text-gray">Owner: {project.owner}</p>
        <p className="text-md font-sans text-gray">
            Total donations: {Web3.utils.fromWei(totalDonations, "ether")} CTF
            {!project.isFinished &&
                <button onClick={donateClick} type="button" className="text-gray-900 bg-gray-100 hover:bg-gray-200 focus:ring-4 focus:outline-none focus:ring-gray-100 font-medium rounded-lg text-sm px-5 py-2.5 text-center inline-flex items-center dark:focus:ring-gray-500 mr-2 mb-2">
                <svg className="w-4 h-4 mr-2 -ml-1 text-[#626890]" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="ethereum" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 512"><path fill="currentColor" d="M311.9 260.8L160 353.6 8 260.8 160 0l151.9 260.8zM160 383.4L8 290.6 160 512l152-221.4-152 92.8z"></path></svg>
                Donate 0.05 CTF
                </button>
            }
        </p>
        <p className="text-md font-sans text-gray">Last baker: {project.lastBaker}</p>
        <p>
            {project.owner == userAddress && <button className="small-button" onClick={withdrawClick}>Withdraw and Finish</button>}
            {project.isFinished && project.lastBaker == userAddress && <button className="small-button" onClick={getAwardClick}>Get Award</button>}
        </p>
    </div>
}