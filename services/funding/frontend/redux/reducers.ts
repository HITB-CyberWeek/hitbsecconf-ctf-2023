import {createSlice, PayloadAction} from "@reduxjs/toolkit";

interface IWeb3State {
    connection?: any;
    userAddress: string;
    platformAddress: string;
}

const initialWeb3State: IWeb3State = {
    connection: null,
    userAddress: "",
    platformAddress: "",
}

export const web3Slice = createSlice({
    name: 'web3',
    initialState: initialWeb3State,
    reducers: {
        connect: (state, action: PayloadAction<any>) => {
            state.connection = action.payload;
        },
        setUserAddress: (state, action: PayloadAction<string>) => {
            state.userAddress = action.payload;
        },
        setPlatformAddress: (state, action: PayloadAction<string>) => {
            state.platformAddress = action.payload;
        },
    }
})

export interface Project {
    id: number;
    error?: string;
    owner?: string;
    address?: string;
    title?: string;
    totalDonations?: string;
    lastBaker?: string;
    isFinished?: boolean;
}

interface IProjectsState {
    projects: Project[];
}

const initialProjectsState: IProjectsState = {
    projects: []
};

export const projectsSlice = createSlice({
    name: 'projects',
    initialState: initialProjectsState,
    reducers: {
        set: (state, action: PayloadAction<Project[]>) => {
            state.projects = action.payload;
        },
        add: (state, action: PayloadAction<Project>) => {
            state.projects.unshift(action.payload);
        }
    }
});

interface IUserState {
    isAuthenticated: boolean;
    userId?: number;
    address?: string;
}

const initialUserState: IUserState = {
    isAuthenticated: false
};

export const userSlice = createSlice({
    name: 'user',
    initialState: initialUserState,
    reducers: {
        authenticate: (state, action: PayloadAction<{ userId: number, address: string }>) => {
            state.isAuthenticated = true;
            state.userId = action.payload.userId;
            state.address = action.payload.address;
        },
        logout: state => {
            state.isAuthenticated = false;
        }
    }
})
