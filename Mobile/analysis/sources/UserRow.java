package com.ctf.loi;

/* compiled from: LocalDbHelper.kt */
@kotlin.Metadata(d1 = {"\u0000 \n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0002\b\u000f\n\u0002\u0010\u000b\n\u0002\b\u0004\b\u0087\b\u0018\u00002\u00020\u0001B'\u0012\u0006\u0010\u0002\u001a\u00020\u0003\u0012\u0006\u0010\u0004\u001a\u00020\u0005\u0012\u0006\u0010\u0006\u001a\u00020\u0005\u0012\u0006\u0010\u0007\u001a\u00020\u0003¢\u0006\u0004\b\b\u0010\tJ\t\u0010\u000f\u001a\u00020\u0003HÆ\u0003J\t\u0010\u0010\u001a\u00020\u0005HÆ\u0003J\t\u0010\u0011\u001a\u00020\u0005HÆ\u0003J\t\u0010\u0012\u001a\u00020\u0003HÆ\u0003J1\u0010\u0013\u001a\u00020\u00002\b\b\u0002\u0010\u0002\u001a\u00020\u00032\b\b\u0002\u0010\u0004\u001a\u00020\u00052\b\b\u0002\u0010\u0006\u001a\u00020\u00052\b\b\u0002\u0010\u0007\u001a\u00020\u0003HÆ\u0001J\u0013\u0010\u0014\u001a\u00020\u00152\b\u0010\u0016\u001a\u0004\u0018\u00010\u0001HÖ\u0003J\t\u0010\u0017\u001a\u00020\u0003HÖ\u0001J\t\u0010\u0018\u001a\u00020\u0005HÖ\u0001R\u0011\u0010\u0002\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\n\u0010\u000bR\u0011\u0010\u0004\u001a\u00020\u0005¢\u0006\b\n\u0000\u001a\u0004\b\f\u0010\rR\u0011\u0010\u0006\u001a\u00020\u0005¢\u0006\b\n\u0000\u001a\u0004\b\u000e\u0010\rR\u0011\u0010\u0007\u001a\u00020\u0003¢\u0006\b\n\u0000\u001a\u0004\b\u0007\u0010\u000b¨\u0006\u0019"}, d2 = {"Lcom/ctf/loi/UserRow;", "", "id", "", androidx.autofill.HintConstants.AUTOFILL_HINT_NAME, "", "email", "isAdmin", "<init>", "(ILjava/lang/String;Ljava/lang/String;I)V", "getId", "()I", "getName", "()Ljava/lang/String;", "getEmail", "component1", "component2", "component3", "component4", "copy", "equals", "", "other", "hashCode", "toString", "app_debug"}, k = 1, mv = {2, 0, 0}, xi = 48)
/* loaded from: classes4.dex */
public final /* data */ class UserRow {
    public static final int $stable = 0;
    private final java.lang.String email;
    private final int id;
    private final int isAdmin;
    private final java.lang.String name;

    public static /* synthetic */ com.ctf.loi.UserRow copy$default(com.ctf.loi.UserRow userRow, int i, java.lang.String str, java.lang.String str2, int i2, int i3, java.lang.Object obj) {
        if ((i3 & 1) != 0) {
            i = userRow.id;
        }
        if ((i3 & 2) != 0) {
            str = userRow.name;
        }
        if ((i3 & 4) != 0) {
            str2 = userRow.email;
        }
        if ((i3 & 8) != 0) {
            i2 = userRow.isAdmin;
        }
        return userRow.copy(i, str, str2, i2);
    }

    /* renamed from: component1, reason: from getter */
    public final int getId() {
        return this.id;
    }

    /* renamed from: component2, reason: from getter */
    public final java.lang.String getName() {
        return this.name;
    }

    /* renamed from: component3, reason: from getter */
    public final java.lang.String getEmail() {
        return this.email;
    }

    /* renamed from: component4, reason: from getter */
    public final int getIsAdmin() {
        return this.isAdmin;
    }

    public final com.ctf.loi.UserRow copy(int id, java.lang.String name, java.lang.String email, int isAdmin) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(name, "name");
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(email, "email");
        return new com.ctf.loi.UserRow(id, name, email, isAdmin);
    }

    public boolean equals(java.lang.Object other) {
        if (this == other) {
            return true;
        }
        if (!(other instanceof com.ctf.loi.UserRow)) {
            return false;
        }
        com.ctf.loi.UserRow userRow = (com.ctf.loi.UserRow) other;
        return this.id == userRow.id && kotlin.jvm.internal.Intrinsics.areEqual(this.name, userRow.name) && kotlin.jvm.internal.Intrinsics.areEqual(this.email, userRow.email) && this.isAdmin == userRow.isAdmin;
    }

    public int hashCode() {
        return (((((java.lang.Integer.hashCode(this.id) * 31) + this.name.hashCode()) * 31) + this.email.hashCode()) * 31) + java.lang.Integer.hashCode(this.isAdmin);
    }

    public java.lang.String toString() {
        return "UserRow(id=" + this.id + ", name=" + this.name + ", email=" + this.email + ", isAdmin=" + this.isAdmin + ")";
    }

    public UserRow(int id, java.lang.String name, java.lang.String email, int isAdmin) {
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(name, "name");
        kotlin.jvm.internal.Intrinsics.checkNotNullParameter(email, "email");
        this.id = id;
        this.name = name;
        this.email = email;
        this.isAdmin = isAdmin;
    }

    public final java.lang.String getEmail() {
        return this.email;
    }

    public final int getId() {
        return this.id;
    }

    public final java.lang.String getName() {
        return this.name;
    }

    public final int isAdmin() {
        return this.isAdmin;
    }
}
