package com.lixingchi.noclearhijack;

import android.content.pm.ApplicationInfo;
import android.util.Log;
import java.lang.reflect.Field;
import io.github.libxposed.api.XposedInterface;
import io.github.libxposed.api.XposedModule;
import io.github.libxposed.api.XposedModuleInterface;

/**
 * Stops the "Clear storage" button in Settings from being redirected to an app's
 * {@code android:manageSpaceActivity}. AOSP Settings shows that button, but when the app declares
 * a manage-space activity its click handler launches the app's own screen instead of clearing data.
 * This module makes the click fall through to the normal clear-data confirmation for every app.
 *
 * <p>Only the Settings process is touched. The clear itself is still
 * {@code ActivityManager.clearApplicationUserData}; this module does not bypass device-admin or
 * {@code DISALLOW_APPS_CONTROL} restrictions.</p>
 */
public final class NoClearHijack extends XposedModule {
    private static final String TAG = "NoClearHijack";
    private static final String SETTINGS_PACKAGE = "com.android.settings";
    private static final String STORAGE_FRAGMENT =
            "com.android.settings.applications.AppStorageSettings";

    @Override
    public void onPackageReady(XposedModuleInterface.PackageReadyParam param) {
        if (!SETTINGS_PACKAGE.equals(param.getPackageName())) {
            detach();
            return;
        }
        try {
            Class<?> fragment = param.getClassLoader().loadClass(STORAGE_FRAGMENT);
            install(fragment, "initDataButtons");
            install(fragment, "handleClearDataClick");
        } catch (Throwable t) {
            log(Log.ERROR, TAG, "install failed", t);
        }
    }

    private void install(Class<?> fragment, String methodName) {
        try {
            hook(fragment.getDeclaredMethod(methodName))
                    .setExceptionMode(XposedInterface.ExceptionMode.PROTECTIVE)
                    .intercept(chain -> {
                        dropManageSpace(chain.getThisObject());
                        return chain.proceed();
                    });
            log(Log.INFO, TAG, "installed on " + fragment.getName() + "#" + methodName);
        } catch (Throwable t) {
            log(Log.WARN, TAG, "skipped " + methodName, t);
        }
    }

    /** Clears the cached ApplicationInfo's manage-space activity so the real clear path is taken. */
    private void dropManageSpace(Object fragment) {
        if (fragment == null) {
            return;
        }
        try {
            Object entry = getField(fragment, "mAppEntry");
            if (entry == null) {
                return;
            }
            Object info = getField(entry, "info");
            if (info instanceof ApplicationInfo) {
                ((ApplicationInfo) info).manageSpaceActivityName = null;
            }
        } catch (Throwable t) {
            log(Log.ERROR, TAG, "could not drop manage-space activity", t);
        }
    }

    private static Object getField(Object target, String name) throws Exception {
        for (Class<?> type = target.getClass(); type != null; type = type.getSuperclass()) {
            try {
                Field field = type.getDeclaredField(name);
                field.setAccessible(true);
                return field.get(target);
            } catch (NoSuchFieldException ignored) {
                // Walk up: the field may be declared on a superclass.
            }
        }
        throw new NoSuchFieldException(name);
    }
}
