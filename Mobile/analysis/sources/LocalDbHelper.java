package com.ctf.loi;

/* compiled from: LocalDbHelper.kt */
@kotlin.Metadata(d1 = {"\u00006\n\u0002\u0018\u0002\n\u0002\u0018\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0003\n\u0002\u0010\u0002\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0002\n\u0002\u0010\b\n\u0002\b\u0004\n\u0002\u0010\u000e\n\u0002\b\u0002\n\u0002\u0018\u0002\n\u0000\b\u0007\u0018\u00002\u00020\u0001B\u000f\u0012\u0006\u0010\u0002\u001a\u00020\u0003¢\u0006\u0004\b\u0004\u0010\u0005J\u0010\u0010\u0006\u001a\u00020\u00072\u0006\u0010\b\u001a\u00020\tH\u0016J \u0010\n\u001a\u00020\u00072\u0006\u0010\b\u001a\u00020\t2\u0006\u0010\u000b\u001a\u00020\f2\u0006\u0010\r\u001a\u00020\fH\u0016J\u0006\u0010\u000e\u001a\u00020\u0007J\u0016\u0010\u000f\u001a\u00020\u00072\u0006\u0010\u0010\u001a\u00020\u00112\u0006\u0010\u0012\u001a\u00020\u0011J\u0010\u0010\u0013\u001a\u0004\u0018\u00010\u00142\u0006\u0010\u0010\u001a\u00020\u0011¨\u0006\u0015"}, d2 = {"Lcom/ctf/loi/LocalDbHelper;", "Landroid/database/sqlite/SQLiteOpenHelper;", "context", "Landroid/content/Context;", "<init>", "(Landroid/content/Context;)V", "onCreate", "", "db", "Landroid/database/sqlite/SQLiteDatabase;", "onUpgrade", "oldVersion", "", "newVersion", "seedAdmin", "createUser", androidx.autofill.HintConstants.AUTOFILL_HINT_NAME, "", "email", "safeFindByName", "Lcom/ctf/loi/UserRow;", "app_debug"}, k = 1, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
public final class LocalDbHelper extends android.database.sqlite.SQLiteOpenHelper {
    public static final int $stable = 0;

    /* JADX WARN: 'super' call moved to the top of the method (can break code semantics) */
    public LocalDbHelper(android.content.Context context) {
        super(context, "loi_local.db", (android.database.sqlite.SQLiteDatabase.CursorFactory) null, 1);
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(context, "context");
    }

    @Override // android.database.sqlite.SQLiteOpenHelper
    public void onCreate(android.database.sqlite.SQLiteDatabase db) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(db, "db");
        db.execSQL("CREATE TABLE users (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    name TEXT,\n    email TEXT,\n    is_admin INTEGER DEFAULT 0\n)");
        db.execSQL("INSERT INTO users (name, email, is_admin) VALUES ('alice', 'alice@example.com', 0)");
        db.execSQL("INSERT INTO users (name, email, is_admin) VALUES ('bob', 'bob@example.com', 0)");
    }

    @Override // android.database.sqlite.SQLiteOpenHelper
    public void onUpgrade(android.database.sqlite.SQLiteDatabase db, int oldVersion, int newVersion) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(db, "db");
        db.execSQL("DROP TABLE IF EXISTS users");
        onCreate(db);
    }

    public final void seedAdmin() {
        android.database.sqlite.SQLiteDatabase sQLiteDatabase;
        android.database.Cursor writableDatabase = getWritableDatabase();
        try {
            sQLiteDatabase = writableDatabase;
            kotlin.jvm.internal.Intrinsics.checkNotNull(sQLiteDatabase);
            sQLiteDatabase.beginTransaction();
        } finally {
            try {
                throw th;
            } finally {
            }
        }
        try {
            try {
                writableDatabase = sQLiteDatabase.rawQuery("SELECT id FROM users WHERE is_admin = 1 LIMIT 1", null);
            } catch (java.lang.Exception e) {
                java.lang.Integer.valueOf(android.util.Log.e("LocalDbHelper", "seedAdmin error: " + e.getMessage()));
            }
            try {
                if (writableDatabase.moveToFirst()) {
                    kotlin.Unit unit = kotlin.Unit.INSTANCE;
                } else {
                    android.content.ContentValues contentValues = new android.content.ContentValues();
                    contentValues.put(androidx.autofill.HintConstants.AUTOFILL_HINT_NAME, "");
                    contentValues.put("email", "admin@local");
                    contentValues.put("is_admin", (java.lang.Integer) 1);
                    java.lang.Long.valueOf(sQLiteDatabase.insert("users", null, contentValues));
                }
                kotlin.io.CloseableKt.closeFinally(writableDatabase, null);
                sQLiteDatabase.setTransactionSuccessful();
                kotlin.io.CloseableKt.closeFinally(writableDatabase, null);
            } finally {
            }
        } finally {
            sQLiteDatabase.endTransaction();
        }
    }

    public final void createUser(java.lang.String name, java.lang.String email) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(name, "name");
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(email, "email");
        android.database.sqlite.SQLiteDatabase writableDatabase = getWritableDatabase();
        try {
            android.database.sqlite.SQLiteDatabase sQLiteDatabase = writableDatabase;
            try {
                java.lang.String str = "INSERT INTO users (name, email, is_admin) VALUES ('" + name + "', '" + email + "', 0);";
                android.util.Log.i("LocalDbHelper", "VULN_INSERT: " + str);
                sQLiteDatabase.execSQL(str);
                kotlin.Unit unit = kotlin.Unit.INSTANCE;
            } catch (java.lang.Exception e) {
                java.lang.Integer.valueOf(android.util.Log.e("LocalDbHelper", "createUserVulnerable error: " + e.getMessage()));
            }
            kotlin.io.CloseableKt.closeFinally(writableDatabase, null);
        } finally {
        }
    }

    public final com.ctf.loi.UserRow safeFindByName(java.lang.String name) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(name, "name");
        android.database.Cursor readableDatabase = getReadableDatabase();
        try {
            java.lang.String lowerCase = name.toLowerCase(java.util.Locale.ROOT);
            kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(lowerCase, "toLowerCase(...)");
            readableDatabase = readableDatabase.rawQuery("SELECT id, name, email, is_admin FROM users WHERE LOWER(name) = ? LIMIT 1", new java.lang.String[]{lowerCase});
            try {
                android.database.Cursor cursor = readableDatabase;
                if (!cursor.moveToFirst()) {
                    kotlin.Unit unit = kotlin.Unit.INSTANCE;
                    kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                    kotlin.Unit unit2 = kotlin.Unit.INSTANCE;
                    kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                    return null;
                }
                int i = cursor.getInt(cursor.getColumnIndexOrThrow("id"));
                java.lang.String string = cursor.getString(cursor.getColumnIndexOrThrow(androidx.autofill.HintConstants.AUTOFILL_HINT_NAME));
                kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(string, "getString(...)");
                java.lang.String string2 = cursor.getString(cursor.getColumnIndexOrThrow("email"));
                kotlin.jvm.internal.Intrinsics.checkNotNullExpressionValue(string2, "getString(...)");
                com.ctf.loi.UserRow userRow = new com.ctf.loi.UserRow(i, string, string2, cursor.getInt(cursor.getColumnIndexOrThrow("is_admin")));
                kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                kotlin.io.CloseableKt.closeFinally(readableDatabase, null);
                return userRow;
            } finally {
            }
        } finally {
        }
    }
}
