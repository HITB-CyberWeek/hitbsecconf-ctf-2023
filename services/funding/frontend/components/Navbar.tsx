import {useAppDispatch, useAppSelector} from "@/redux/store";
import {useEffect, useState} from "react";
import {authenticate, loadUser, logout} from "@/redux/interactions";
import {toastError} from "@/app/toasts";

export default function Navbar()  {
    const dispatch = useAppDispatch();

    const web3Address = useAppSelector(state => state.web3.userAddress)
    const user = useAppSelector(state=> state.user);
    const isAuthenticated = user.isAuthenticated && user.address?.toLowerCase() == web3Address.toLowerCase();
    let [password, setPassword] = useState("");

    useEffect(() => {
        loadUser(dispatch).catch()
    }, [dispatch]);

    const tryToAuthenticate = async () => {
        if (!password) {
            toastError("Password can not be empty");
            return;
        }
        const result = await authenticate(web3Address, password, dispatch);
        if (!result) {
            toastError("Wrong password, try again");
        }
    }

    const tryToLogout = async () => {
        await logout(dispatch);
        setPassword("");
    }

    return (
        <nav className="bg-white border-gray-200 dark:bg-gray-900">
            <div className="flex flex-wrap items-center justify-between mx-auto p-6">
                <a href="/" className="flex items-center navbar-link">
                    <span className="self-center text-2xl font-semibold whitespace-nowrap dark:text-white">HITB CROWD FUNDING</span>
                </a>

                <div className="flex md:flex-row flex-col space-x-6">
                    <div className="p-1 w-64 truncate rounded-full text-greay hover:text-greay ">
                        <span>{isAuthenticated ? user.address : web3Address}</span>
                    </div>

                    {!isAuthenticated && <div className="flex md:order-2">
                        <div className="relative ">
                             <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                                className="block w-full p-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                                placeholder="Password"/>
                        </div>
                    </div>}
                    <div className="flex md:order-2">
                        <div className="relative ">
                            {!isAuthenticated && <button type="button" onClick={tryToAuthenticate}
                                                        className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 text-center mr-3 md:mr-0 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                                Login or register
                            </button>}
                            {isAuthenticated && <button type="button" onClick={tryToLogout}
                                                        className="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 text-center mr-3 md:mr-0 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">
                                Logout
                            </button>}
                        </div>
                    </div>
                </div>
            </div>
        </nav>
    )
}