import { useAppDispatch, useAppSelector } from "@/redux/store";
import ProjectCard from "@/components/ProjectCard";
import { useEffect, useState } from "react";
import { loadProjects } from "@/redux/interactions";
import NewProjectForm from "@/components/NewProjectForm";

export default function Projects() {
    const dispatch = useAppDispatch();
    const projects = useAppSelector(state => state.projects.projects);
    let [loading, setLoading] = useState(true);

    useEffect(() => {
        loadProjects(dispatch).then(() => {setLoading(false)});
    }, [dispatch]);

    return <div className="px-6 py-4 flex flex-col lg:flex-row ">
        <div className="card lg:w-5/12 h-fit my-4">
            <NewProjectForm/>
        </div>
        <div className="lg:w-7/12 my-4 lg:mx-2">
            {projects && projects.map(project => <ProjectCard project={project} key={project.id}/>)}
            {!loading && projects.length == 0 && <h1 className="text-2xl font-bold text-gray-500 text-center font-sans">There are no projects yet</h1>}
        </div>
    </div>
}