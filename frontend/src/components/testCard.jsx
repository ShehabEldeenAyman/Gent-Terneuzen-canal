import React, { useEffect, useState,useRef, use  } from "react";
import { replicateLDES } from "ldes-client";
import { Store } from "n3";
import {ldesState} from "./LDESClientCard";

export function TestCard() {

    useEffect(() => {
        const quads = ldesState.store.getQuads(null, null, null, null);
        console.log("TestCard initialized. Current graph store size:", ldesState.count); //
    }, []);

      return (
    <div >
        <h2>Test Card</h2>
        <p>This is a test card to verify that the LDES client is working correctly.</p>
    </div>
  );
}