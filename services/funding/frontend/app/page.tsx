'use client'

import {useEffect, useState} from "react";
import {useAppSelector} from "@/redux/store";
import ConnectWithMetaMask from "@/components/ConnectWithMetaMask";
import Projects from "@/components/Projects";
import Navbar from "@/components/Navbar";


export default function Home() {
    const address = useAppSelector(state => state.web3.userAddress);
    const [ connected, setConnected ] = useState(false);

    useEffect(() => {
        if (address) {
            console.log(address);
            setConnected(true);
        }
    }, [address]);

    return connected
        ? <><Navbar/><Projects/></>
        : <ConnectWithMetaMask/>;
}