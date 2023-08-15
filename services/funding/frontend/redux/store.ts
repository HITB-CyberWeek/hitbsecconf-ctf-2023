import { projectsSlice, userSlice, web3Slice } from "./reducers"
import { configureStore } from "@reduxjs/toolkit";
import { TypedUseSelectorHook, useDispatch, useSelector } from "react-redux";

export const store = configureStore({
    reducer: {
        web3: web3Slice.reducer,
        projects: projectsSlice.reducer,
        user: userSlice.reducer,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: {
                ignoredActions: ['web3/connect'],
                ignoredActionPaths: ['web3.connection'],
                ignoredPaths: ['web3.connection'],
            },
        }),
});

export type AppRootState = ReturnType<typeof store.getState>

export type AppDispatch = typeof store.dispatch
type DispatchFunc = () => AppDispatch

// Use throughout the app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch: DispatchFunc = useDispatch
export const useAppSelector: TypedUseSelectorHook<AppRootState> = useSelector
