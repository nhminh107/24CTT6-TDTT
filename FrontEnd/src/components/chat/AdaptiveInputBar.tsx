import React from "react";
import StepLocation from "./StepLocation";
import StepBudget from "./StepBudget";
import StepPreferences from "./StepPreferences";
import StepChatFree from "./StepChatFree";

export const STEPS = {
  STEP_LOCATION: "STEP_LOCATION",
  STEP_BUDGET: "STEP_BUDGET",
  STEP_PREFERENCES: "STEP_PREFERENCES",
  STEP_CHAT_FREE: "STEP_CHAT_FREE",
} as const;

export type Step = typeof STEPS[keyof typeof STEPS];

interface AdaptiveInputBarProps {
  currentStep?: Step;
  onUpdate: (data: any) => void;
  onNext: () => void;
}

export default function AdaptiveInputBar({ currentStep, onUpdate, onNext }: AdaptiveInputBarProps) {
  const step: Step = currentStep || STEPS.STEP_LOCATION;

  // Tính % tiến trình để làm thanh Progress Bar nhỏ phía trên
  const getProgress = () => {
    const steps = Object.values(STEPS);
    return ((steps.indexOf(step) + 1) / steps.length) * 100;
  };

  const renderStep = (): React.ReactNode => {
    switch (step) {
      case STEPS.STEP_LOCATION:    return <StepLocation onUpdate={onUpdate} onNext={onNext} />;
      case STEPS.STEP_BUDGET:      return <StepBudget onUpdate={onUpdate} onNext={onNext} />;
      case STEPS.STEP_PREFERENCES: return <StepPreferences onUpdate={onUpdate} onNext={onNext} />;
      case STEPS.STEP_CHAT_FREE:   return <StepChatFree onUpdate={onUpdate} onNext={onNext} />;
      default: return null;
    }
  };

  return (
  <div
    className="
      relative w-full
      animate-in fade-in
      slide-in-from-bottom-4
      duration-500
    "
  >

    {/* Step content */}
    <div>
      {renderStep()}
    </div>

    {/* Small helper text */}
    <p
      className="
        mt-3 text-center
        text-[10px]
        font-medium
        uppercase tracking-widest
        text-orange-400/60
      "
    >
      {step.replace(
        "STEP_",
        "Personalizing Your "
      )}
    </p>
  </div>
);
}