import { CAMERA_FRAMES, VIEW_MODE_TRANSITION_MS } from "./constants.js";
import { applyComputedTransform, computeTransform } from "./transform.js";

function easeInOutCubic(value) {
  return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function lerpAngle(start, end, progress) {
  const delta = Math.atan2(Math.sin(end - start), Math.cos(end - start));
  return start + delta * progress;
}

export function createTransition(model, targetTransform, now) {
  return {
    startPosition: model.position.clone(),
    startRotationY: model.rotation.y,
    startScale: model.scale.x,
    targetPosition: targetTransform.position.clone(),
    targetRotationY: targetTransform.rotationY,
    targetScale: targetTransform.scale,
    startedAt: now,
  };
}

export function updateModelTransition(record, now) {
  if (!record.transition) {
    return;
  }

  const elapsed = now - record.transition.startedAt;
  const progress = Math.min(elapsed / VIEW_MODE_TRANSITION_MS, 1);
  const eased = easeInOutCubic(progress);

  record.model.position.lerpVectors(
    record.transition.startPosition,
    record.transition.targetPosition,
    eased
  );
  record.model.rotation.y = lerpAngle(
    record.transition.startRotationY,
    record.transition.targetRotationY,
    eased
  );
  const scale =
    record.transition.startScale +
    (record.transition.targetScale - record.transition.startScale) * eased;
  record.model.scale.setScalar(scale);

  if (progress >= 1) {
    applyComputedTransform(record.model, {
      position: record.transition.targetPosition,
      rotationY: record.transition.targetRotationY,
      scale: record.transition.targetScale,
    });
    record.transition = null;
  }
}

export function createCameraTransition(camera, controls, targetFrame, now) {
  return {
    startPosition: camera.position.clone(),
    startTarget: controls.target.clone(),
    targetPosition: targetFrame.position.clone(),
    targetTarget: targetFrame.target.clone(),
    startedAt: now,
  };
}

export function updateCameraTransition(state, now) {
  if (!state.cameraTransition) {
    return;
  }

  const elapsed = now - state.cameraTransition.startedAt;
  const progress = Math.min(elapsed / VIEW_MODE_TRANSITION_MS, 1);
  const eased = easeInOutCubic(progress);

  state.camera.position.lerpVectors(
    state.cameraTransition.startPosition,
    state.cameraTransition.targetPosition,
    eased
  );
  state.controls.target.lerpVectors(
    state.cameraTransition.startTarget,
    state.cameraTransition.targetTarget,
    eased
  );

  if (progress >= 1) {
    state.camera.position.copy(state.cameraTransition.targetPosition);
    state.controls.target.copy(state.cameraTransition.targetTarget);
    state.cameraTransition = null;
  }
}

export function updateTransitions(state) {
  const now = performance.now();
  for (const record of state.records) {
    updateModelTransition(record, now);
  }
  updateCameraTransition(state, now);
}

export function transitionToViewMode(state, viewMode, setModeButtonState) {
  if (state.currentViewMode === viewMode) {
    return;
  }

  state.currentViewMode = viewMode;
  setModeButtonState(state.container, viewMode);

  const now = performance.now();
  for (const record of state.records) {
    record.transition = createTransition(record.model, computeTransform(record.cell, viewMode), now);
  }
  state.cameraTransition = createCameraTransition(
    state.camera,
    state.controls,
    CAMERA_FRAMES[viewMode] ?? CAMERA_FRAMES.original,
    now
  );
}
