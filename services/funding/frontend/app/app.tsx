"use client";

import {AppDispatch, store, useAppDispatch} from "@/redux/store";
import { Provider } from "react-redux";
import React, {useEffect} from "react";
import {loadWeb3} from "@/redux/interactions";

async function loadBlockchain(dispatch: AppDispatch) {
    const web3 = await loadWeb3(dispatch);
    // const account = await loadUserAddress(web3,dispatch)
    // const crowdFundingContract = await loadCrowdFundingContract(web3,dispatch)
    // await getAllFunding(crowdFundingContract,web3,dispatch)
}

function Wrapper({ children }: { children: React.ReactNode }) {
    const dispatch = useAppDispatch();
    useEffect( () => {loadBlockchain(dispatch).then()}, [])

    return <>{children}</>
}

export function AppContainer({ children }: { children: React.ReactNode }) {
    return <Provider store={store}><Wrapper>{children}</Wrapper></Provider>;
}