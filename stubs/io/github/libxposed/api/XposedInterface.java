package io.github.libxposed.api;

import java.lang.reflect.Executable;
import java.util.List;

/**
 * Compile-only declaration of the framework's API 102 surface. See
 * {@link XposedModuleInterface} for the package rules.
 */
public interface XposedInterface {
    interface Hooker {
        Object intercept(Chain chain) throws Throwable;
    }

    interface Chain {
        Executable getExecutable();
        Object getThisObject();
        List<Object> getArgs();
        Object getArg(int index);
        Object proceed() throws Throwable;
        Object proceed(Object[] args) throws Throwable;
        Object proceedWith(Object thisObject) throws Throwable;
        Object proceedWith(Object thisObject, Object[] args) throws Throwable;
    }

    interface HookHandle {
        Executable getExecutable();
        void unhook();
    }

    enum ExceptionMode {
        DEFAULT,
        PROTECTIVE,
        PASSTHROUGH
    }

    interface HookBuilder {
        HookBuilder setPriority(int priority);
        HookBuilder setExceptionMode(ExceptionMode mode);
        HookHandle intercept(Hooker hooker);
    }

    HookBuilder hook(Executable origin);

    void log(int priority, String tag, String msg);

    void log(int priority, String tag, String msg, Throwable tr);
}
