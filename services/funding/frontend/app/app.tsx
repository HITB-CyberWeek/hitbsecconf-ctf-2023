"use client";

import { store, useAppDispatch } from "@/redux/store";
import { Provider } from "react-redux";
import React, { useEffect } from "react";

function Wrapper({ children }: { children: React.ReactNode }) {
    const dispatch = useAppDispatch();

    useEffect(() => {
        if (window.ethereum) {
            window.ethereum.on("accountsChanged", () => {window.location.reload()});
            window.ethereum.on("chainChanged", () => {window.location.reload()});
        }
    }, [dispatch]);

    return children;
}

export function AppContainer({ children }: { children: React.ReactNode }) {
    return <Provider store={store}><Wrapper>{children}</Wrapper></Provider>;
}