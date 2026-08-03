/** Global app state via React context. */

import { createContext, useContext, useState, type ReactNode } from "react";

export interface ChapterData {
  index: number;
  title: string;
  text: string;
  sml?: string;
}

export interface RoleData {
  name: string;
  gender: string;
  age: string;
  aliases: string[];
  voice?: VoiceAssignment;
}

export interface VoiceAssignment {
  engine: string;
  voice_id: string;
  reference_audio?: string;
  pitch?: number;
  speed?: number;
}

export interface LLMConfig {
  provider: string;
  base_url: string;
  api_key: string;
  model: string;
  temperature: number;
}

export interface EngineConfig {
  [engine_id: string]: Record<string, string>;
}

interface AppState {
  // Book
  bookTitle: string;
  bookAuthor: string;
  chapters: ChapterData[];
  setBook: (title: string, author: string, chapters: ChapterData[]) => void;

  // Roles
  roles: RoleData[];
  setRoles: (roles: RoleData[]) => void;

  // LLM
  llmConfig: LLMConfig;
  setLLMConfig: (cfg: LLMConfig) => void;

  // TTS engine configs
  engineConfigs: EngineConfig;
  setEngineConfigs: (cfg: EngineConfig) => void;

  // Output
  outputFormat: string;
  setOutputFormat: (fmt: string) => void;

  // Reset
  reset: () => void;
}

const defaultState: Omit<AppState, "setBook" | "setRoles" | "setLLMConfig" | "setEngineConfigs" | "setOutputFormat" | "reset"> = {
  bookTitle: "",
  bookAuthor: "",
  chapters: [],
  roles: [],
  llmConfig: {
    provider: "openai_compat",
    base_url: "https://api.deepseek.com/v1",
    api_key: "",
    model: "deepseek-chat",
    temperature: 0.3,
  },
  engineConfigs: {},
  outputFormat: "m4b",
};

const AppContext = createContext<AppState | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [bookTitle, setBookTitle] = useState(defaultState.bookTitle);
  const [bookAuthor, setBookAuthor] = useState(defaultState.bookAuthor);
  const [chapters, setChapters] = useState<ChapterData[]>(defaultState.chapters);
  const [roles, setRoles] = useState<RoleData[]>(defaultState.roles);
  const [llmConfig, setLLMConfig] = useState<LLMConfig>(defaultState.llmConfig);
  const [engineConfigs, setEngineConfigs] = useState<EngineConfig>(defaultState.engineConfigs);
  const [outputFormat, setOutputFormat] = useState(defaultState.outputFormat);

  const setBook = (title: string, author: string, chs: ChapterData[]) => {
    setBookTitle(title);
    setBookAuthor(author);
    setChapters(chs);
  };

  const reset = () => {
    setBookTitle("");
    setBookAuthor("");
    setChapters([]);
    setRoles([]);
  };

  return (
    <AppContext.Provider
      value={{
        bookTitle,
        bookAuthor,
        chapters,
        setBook,
        roles,
        setRoles,
        llmConfig,
        setLLMConfig,
        engineConfigs,
        setEngineConfigs,
        outputFormat,
        setOutputFormat,
        reset,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
