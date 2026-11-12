/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.seeyon.boot.annotation.Custom
 *  com.seeyon.boot.annotation.CustomAttribute
 *  com.seeyon.boot.annotation.EnumInfo
 *  com.seeyon.boot.enums.Messageable
 */
package com.seeyon.bpm.dto.message;

import com.seeyon.boot.annotation.Custom;
import com.seeyon.boot.annotation.CustomAttribute;
import com.seeyon.boot.annotation.EnumInfo;
import com.seeyon.boot.enums.Messageable;

@EnumInfo(value="\u6d88\u606f\u7c7b\u578b", customs={@Custom(properties={@CustomAttribute(name="appName", value="bpm")})}, excludes={"NONE"})
public enum BpmMqDataType implements Messageable
{
    NONE(-1),
    TIMER_ACTIVIY_DELAY_MESSAGE(0),
    TIMER_START_DELAY_MESSAGE(1),
    PROCESS_OVERTIME(2),
    ACTIVITY_OVERTIME(3),
    DETECTION(4),
    PROCESS_STARTED(10),
    PROCESS_FINISHED(11),
    PROCESS_CANCELED(12),
    PROCESS_STOPPED(13),
    CUSTOM_NODE_EVENT(14),
    TEMPLATE_SYNC(15),
    STEP_BACK(16),
    PROCESS_SUBMIT(17),
    APPROVAL_RESULT(18),
    BUSINESS_ACTIVITY_SEND(19),
    BUSINESS_ACTIVITY_RECEIVE(20),
    RETRIEVE(21),
    TRANSFER(22),
    CONSULT(23),
    TEMPORARY_PENDING(24),
    SUPERVISE_CHANGE_PROCESS(25),
    INFORM(26),
    HASTEN(27),
    VIP_SUPERVISE_CREATE(28),
    VIP_SUPERVISE_CANCEL(29),
    PROCESS_RELIVE(30),
    PROCESS_DRAFT(31),
    PROCESS_PAUSE(32),
    PROCESS_CANCEL_PAUSE(33),
    ABNORMAL_REPORT(34),
    PROCESS_DELETE(35),
    MULTI_WRITE(36),
    CHANGE_OPINION(37),
    CONSULTOR_SETTING(38);

    private int code;

    private BpmMqDataType(int code) {
        this.code = code;
    }

    public int code() {
        return this.code;
    }
}
