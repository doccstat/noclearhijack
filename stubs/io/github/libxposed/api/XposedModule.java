package io.github.libxposed.api;

import java.lang.reflect.Executable;

/**
 * Compile-only declaration of the framework's API 102 surface. See
 * {@link XposedModuleInterface} for the package rules.
 */
public abstract class XposedModule implements XposedModuleInterface, XposedInterface {
    public void detach() {
    }

    @Override
    public HookBuilder hook(Executable origin) {
        throw new UnsupportedOperationException();
    }

    @Override
    public void log(int priority, String tag, String msg) {
    }

    @Override
    public void log(int priority, String tag, String msg, Throwable tr) {
    }
}
