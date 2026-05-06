import { useCallback, useEffect, useRef, useState } from "react";

import { RECIPE_NOTES_SAVE_DEBOUNCE_MS } from "../EditorFoundation/constants";
import { loadRecipeNotes, saveRecipeNotes } from "../RecipeGraph/notesStorage";

export function useRecipeGraphNotes(recipeId: number) {
  const [notes, setNotes] = useState("");
  const notesSaveTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  useEffect(() => {
    if (notesSaveTimerRef.current !== undefined) {
      clearTimeout(notesSaveTimerRef.current);
      notesSaveTimerRef.current = undefined;
    }
    setNotes(loadRecipeNotes(recipeId));
  }, [recipeId]);

  const handleNotesChange = useCallback(
    (text: string) => {
      setNotes(text);
      if (notesSaveTimerRef.current !== undefined) {
        clearTimeout(notesSaveTimerRef.current);
      }
      notesSaveTimerRef.current = setTimeout(() => {
        saveRecipeNotes(recipeId, text);
      }, RECIPE_NOTES_SAVE_DEBOUNCE_MS);
    },
    [recipeId],
  );

  return { notes, handleNotesChange };
}
