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
            <div className="max-w-screen-xl flex flex-wrap items-center justify-between mx-auto p-4">
                <a href="/" className="flex items-center">
                    <span className="self-center text-2xl font-semibold whitespace-nowrap dark:text-white">HITB CROWD FUNDING</span>
                </a>

                <div className="p-1 w-64 truncate rounded-full text-greay hover:text-greay ">
                    <span>{isAuthenticated ? user.address : web3Address}</span>
                </div>

                <div className="flex md:order-2">
                    <div className="relative ">
                        {!isAuthenticated && <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                               className="block w-full p-2 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
                               placeholder="Password"/>}

                    </div>
                </div>
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
        </nav>
    )

    return (
        <div>
            <nav className="bg-[#F7F5F2]">
                <div className="max-w-7xl mx-auto px-2 sm:px-6 lg:px-8">
                    <div className="relative flex items-center justify-between h-16">
                        <div className="flex-1 flex items-center justify-center sm:items-stretch sm:justify-start">
                            <div className="flex-shrink-0 flex items-center">
                                <h4 className='font-mono text-xl text-greay font-bold hidden lg:block'>HITB CROWD FUNDING</h4>
                            </div>
                            <div className="hidden sm:block sm:ml-6">
                                <div className="flex space-x-4">
                                    {/*<Link href="/dashboard"  ><span className={`${router.pathname === "/dashboard"?"bg-[#F7C984]":""} text-greay px-3 py-2 rounded-md text-sm font-medium hover:cursor-pointer hover:bg-[#F7C984] hover:text-greay`}>Dashboard</span></Link>*/}
                                    {/*<Link href="/my-contributions"><span className={`${router.pathname === "/my-contributions"?"bg-[#F7C984]":""} text-greay px-3 py-2 rounded-md text-sm font-medium hover:cursor-pointer hover:bg-[#F7C984] hover:text-greay`}>My contribution</span></Link>*/}
                                </div>
                            </div>
                        </div>
                        <div className="absolute inset-y-0 right-0 flex items-center pr-2 sm:static sm:inset-auto sm:ml-6 sm:pr-0">
                            <div className="p-1 w-64 truncate rounded-full text-greay hover:text-greay ">
                                <span>{isAuthenticated ? user.address : web3Address}</span>
                            </div>
                            {!isAuthenticated && <input type="password" name="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" className="input w-48"/>}
                            {!isAuthenticated && <button type="button" className="button" aria-expanded="false" aria-haspopup="true" onClick={tryToAuthenticate}>
                                Register or login
                            </button>}
                            {isAuthenticated && <button type="button" className="button" aria-expanded="false" aria-haspopup="true" onClick={() => logout(dispatch)}>
                                Logout
                            </button>}

                        </div>
                    </div>
                </div>
            </nav>

        </div>
    )
}