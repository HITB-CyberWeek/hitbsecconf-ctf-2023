import {useAppDispatch, useAppSelector} from "@/redux/store";
import {FormEvent, useEffect, useState} from "react";
import {toastError, toastSuccess} from "@/app/toasts";
import {createProjectContract, createProjectInApi, loadPlatformAddress} from "@/redux/interactions";

export default function NewProjectForm() {
    const web3 = useAppSelector(state=> state.web3.connection);
    const userAddress = useAppSelector(state=> state.web3.userAddress);
    const platformAddress = useAppSelector(state => state.web3.platformAddress);

    const dispatch = useAppDispatch()

    const [title,setTitle] = useState("");
    const [award,setAward] = useState("");
    const [btnLoading,setBtnLoading] = useState(false);

    useEffect(() => {
        loadPlatformAddress(dispatch).catch();
    }, [dispatch]);


    const startProject = async (e: FormEvent) =>{
        e.preventDefault();
        setBtnLoading(true)

        const onSuccess = (address: string) =>{
            setBtnLoading(false);
            setTitle("");
            setAward("");
            toastSuccess(`New project added at address ${address} 🎉`);
        }

        try {
            const address = await createProjectContract(web3, userAddress, platformAddress, title);
            if (!address)
                throw new Error('Can not create a smart contract, sorry.')
            console.log(`Created a contract at ${address}`);
            await createProjectInApi(address, award, dispatch);
            onSuccess(address);
        } catch (e) {
            setBtnLoading(false);
            toastError(e instanceof Error ? e.message : e as string);
        }

    }

    return (
        <form className="space-y-6" onSubmit={startProject}>
            <h5 className="text-xl font-medium text-gray-900 dark:text-white">Start a new project</h5>
            <div>
                <label htmlFor="title" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Title</label>
                <input type="text" name="title" id="title"
                       className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
                       placeholder="Amazing CTF"
                       value={title} onChange={e => setTitle(e.target.value)}
                       required/>
            </div>
            <div>
                <label htmlFor="award" className="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Award</label>
                <input type="text" name="award" id="award"
                       className="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white"
                       placeholder="Award for the latest baker"
                       value={award} onChange={e => setAward(e.target.value)}
                       required/>
            </div>
            <button type="submit"
                    disabled={btnLoading}
                    className="w-full text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                Add project
            </button>
        </form>
    )
}