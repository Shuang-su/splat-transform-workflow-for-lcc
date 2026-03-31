/* eslint-disable no-unused-vars */
interface Window {
    getCameraPose?: () => {
        mode: string,
        position: [number, number, number],
        target: [number, number, number],
        angles: [number, number, number],
        distance: number,
        fov: number
    } | null;

    logCameraPose?: () => {
        mode: string,
        position: [number, number, number],
        target: [number, number, number],
        angles: [number, number, number],
        distance: number,
        fov: number
    } | null;

    sse: {
        poster?: HTMLImageElement,
        settings: Promise<object>,
        contentUrl: string,
        contents: ArrayBuffer,
        params: Record<string, string>
    }

    firstFrame?: () => void;

    scrubTo?: (time: number) => Promise<void>;

    animationDuration?: number;
}

declare module 'playcanvas/scripts/esm/xr-controllers.mjs' {
    const XrControllers: any;
    export { XrControllers };
}

declare module 'playcanvas/scripts/esm/xr-navigation.mjs' {
    const XrNavigation: any;
    export { XrNavigation };
}

declare module '*.html' {
    const content: string;
    export default content;
}

declare module '*.css' {
    const content: string;
    export default content;
}

declare module '*.js' {
    const content: string;
    export default content;
}
