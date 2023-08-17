import { useAppDispatch, useAppSelector } from "@/redux/store";
import { FormEvent, useEffect, useState } from "react";
import { toastError, toastSuccess } from "@/app/toasts";
import { createProjectContract, createProjectInApi, loadPlatformAddress } from "@/redux/interactions";

export default function NewProjectForm() {
    const web3 = useAppSelector(state=> state.web3.connection);
    const userAddress = useAppSelector(state=> state.web3.userAddress);
    const platformAddress = useAppSelector(state => state.web3.platformAddress);
    const isAuthenticated = useAppSelector(state => state.user.isAuthenticated);

    const dispatch = useAppDispatch()

    const [title, setTitle] = useState("");
    const [reward, setReward] = useState("");
    const [btnLoading, setBtnLoading] = useState(false);

    useEffect(() => {
        loadPlatformAddress(dispatch).catch();
    }, [dispatch]);


    const startProject = async (e: FormEvent) => {
        e.preventDefault();
        setBtnLoading(true);

        const onSuccess = (address: string) => {
            setBtnLoading(false);
            toastSuccess(<span>New project <b>{title}</b> added at address <b>{address}</b> 🎉</span>);
            setTitle("");
            setReward("");
        }

        try {
            const address = await createProjectContract(web3, userAddress, platformAddress, title);
            if (!address)
                throw new Error('Can not create a smart contract, sorry.')
            await createProjectInApi(address, reward, dispatch);
            onSuccess(address);
        } catch (e) {
            setBtnLoading(false);
            console.log(e);
            toastError(e instanceof Error ? e.message : e as string);
        }

    }

    return (
        <form className="space-y-6" onSubmit={startProject}>
            <h5 className="text-xl font-medium text-gray-900 dark:text-white">Start donation project</h5>
            <div className="relative z-0">
                <input type="text" id="title" className="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder=" " required value={title} onChange={e => setTitle(e.target.value)}/>
                <label htmlFor="title" className="absolute text-sm text-gray-500 dark:text-gray-400 duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:left-0 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">Title</label>
            </div>
            <div className="relative z-0">
                <input type="text" id="reward" aria-describedby="reward_helper_text" className="block py-2.5 px-0 w-full text-sm text-gray-900 bg-transparent border-0 border-b-2 border-gray-300 appearance-none dark:text-white dark:border-gray-600 dark:focus:border-blue-500 focus:outline-none focus:ring-0 focus:border-blue-600 peer" placeholder=" " required value={reward} onChange={e => setReward(e.target.value)}/>
                <label htmlFor="reward" className="absolute text-sm text-gray-500 dark:text-gray-400 duration-300 transform -translate-y-6 scale-75 top-3 -z-10 origin-[0] peer-focus:left-0 peer-focus:text-blue-600 peer-focus:dark:text-blue-500 peer-placeholder-shown:scale-100 peer-placeholder-shown:translate-y-0 peer-focus:scale-75 peer-focus:-translate-y-6">Reward for last baker</label>
                <p id="reward_helper_text" className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    The individual who donates to this project before you withdraw the funds will be eligible for this reward.
                </p>
            </div>

            {isAuthenticated && <div>
                <button type="submit" disabled={btnLoading}
                        className="w-full text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                    Add project
                </button>
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    By clicking this button, you will create a smart contract. 
                    Others can donate money to this contract, and you can withdraw the donated funds at any time.
                </p>
            </div>}
            {!isAuthenticated && <div>
                <button type="submit" className="w-full text-white bg-blue-400 dark:bg-blue-500 cursor-not-allowed font-medium rounded-lg text-sm px-5 py-2.5 text-center" disabled>
                    Add project
                </button>
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    You must authenticate with your Ethereum address (at the right top corner) first.
                    If it's your first visit, you can use any password.
                </p>
            </div>}
        </form>
    )
}