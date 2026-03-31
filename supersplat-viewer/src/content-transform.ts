import { Quat, Vec3 } from 'playcanvas';

type ContentRotation = [number, number, number] | undefined;

const DEFAULT_CONTENT_ROTATION: [number, number, number] = [0, 0, 180];

const quat = new Quat();
const invQuat = new Quat();

const resolveContentRotation = (contentRotation?: ContentRotation) => {
    return contentRotation ?? DEFAULT_CONTENT_ROTATION;
};

const hasContentRotationOverride = (contentRotation?: ContentRotation) => {
    const resolved = resolveContentRotation(contentRotation);
    return resolved[0] !== DEFAULT_CONTENT_ROTATION[0] ||
        resolved[1] !== DEFAULT_CONTENT_ROTATION[1] ||
        resolved[2] !== DEFAULT_CONTENT_ROTATION[2];
};

const setQuat = (contentRotation: ContentRotation, out: Quat) => {
    const [x, y, z] = resolveContentRotation(contentRotation);
    return out.setFromEulerAngles(x, y, z);
};

const worldToContentPoint = (contentRotation: ContentRotation, point: Vec3, out: Vec3) => {
    setQuat(contentRotation, invQuat).invert().transformVector(point, out);
    return out;
};

const worldToContentDirection = (contentRotation: ContentRotation, direction: Vec3, out: Vec3) => {
    setQuat(contentRotation, invQuat).invert().transformVector(direction, out);
    return out;
};

const contentToWorldPoint = (contentRotation: ContentRotation, point: Vec3, out: Vec3) => {
    setQuat(contentRotation, quat).transformVector(point, out);
    return out;
};

const contentToWorldDirection = (contentRotation: ContentRotation, direction: Vec3, out: Vec3) => {
    setQuat(contentRotation, quat).transformVector(direction, out);
    return out;
};

export {
    DEFAULT_CONTENT_ROTATION,
    hasContentRotationOverride,
    resolveContentRotation,
    worldToContentPoint,
    worldToContentDirection,
    contentToWorldPoint,
    contentToWorldDirection
};

export type { ContentRotation };
