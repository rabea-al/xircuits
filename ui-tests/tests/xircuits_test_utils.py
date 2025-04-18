from playwright.sync_api import Page

def fill_literal_string_input_and_submit(page: Page, text: str = "Hello Test!"):
    print(f"Filling Literal String input with: {text}")
    page.wait_for_selector("textarea[name='New Literal Input']")
    page.fill("textarea[name='New Literal Input']", text)
    page.click("div.jp-Dialog-buttonLabel:has-text('Submit')")
    page.click(".xircuits-canvas")  
    page.wait_for_timeout(500)

def verify_new_port_spawned(
    page: Page, node_name: str, port_name: str, timeout: int = 5000
) -> None:
    """
    Waits for the new port to be attached to the DOM and verifies its existence.
    Does not rely on visibility since the port may be off-screen.
    """
    selector = (
        f"div.node[data-default-node-name='{node_name}'] "
        f"div.port[data-name='{port_name}']"
    )
    page.wait_for_selector(selector, state="attached", timeout=timeout)
    assert page.locator(selector).count() > 0, (
        f"Port '{port_name}' was NOT created for node '{node_name}'."
    )
    print(f"Port '{port_name}' is present for node '{node_name}'.")


def verify_port_not_spawned(
    page: Page, node_name: str, port_name: str, timeout: int = 5000
) -> None:
    """
    Waits for the port to be detached from the DOM and verifies its absence.
    """
    selector = (
        f"div.node[data-default-node-name='{node_name}'] "
        f"div.port[data-name='{port_name}']"
    )
    try:
        page.wait_for_selector(selector, state="detached", timeout=timeout)
    except TimeoutError:
        pass

    assert page.locator(selector).count() == 0, (
        f"Port '{port_name}' unexpectedly PRESENT for node '{node_name}'."
    )
    print(f"Port '{port_name}' is absent for node '{node_name}' as expected.")

def simulate_drag_component_from_library(page: Page, library_name: str, component_name: str) -> None:
    """
    Opens the specified library and drags the specified component onto the canvas.

    :param page: The Playwright page object.
    :param library_name: Name of the library containing the component (e.g. "GRADIO" or "GENERAL").
    :param component_name: Name of the component to drag (e.g. "GradioInterface" or "Literal String").
    """
    print(f"Opening library: {library_name}")
    page.wait_for_selector("[data-id='table-of-contents']")
    page.click("[data-id='table-of-contents']")
    page.wait_for_selector("[data-id='xircuits-component-sidebar']")
    page.click("[data-id='xircuits-component-sidebar']")
    # Click on the library by visible text
    page.get_by_text(library_name, exact=True).click()
    page.wait_for_timeout(1000)  # Wait a bit for content to appear

    print(f"Dragging component: {component_name} from library {library_name} to canvas...")
    page.evaluate(f"""
    () => {{
      // Find the draggable element that contains the desired text
      const source = [...document.querySelectorAll("[draggable='true']")]
        .find(el => el.innerText.includes("{component_name}"));
      // Target the canvas (ensure this selector matches the actual element)
      const target = document.querySelector(".xircuits-canvas");
  
      if (!source || !target) {{
          console.warn("Component or canvas not found.");
          return;
      }}
  
      // Add dragTo method to HTMLElement
      HTMLElement.prototype.dragTo = function(targetElement) {{
          const dataTransfer = new DataTransfer();
          this.dispatchEvent(new DragEvent('dragstart', {{ dataTransfer, bubbles: true }}));
          targetElement.dispatchEvent(new DragEvent('dragenter', {{ dataTransfer, bubbles: true }}));
          targetElement.dispatchEvent(new DragEvent('dragover', {{ dataTransfer, bubbles: true }}));
          targetElement.dispatchEvent(new DragEvent('drop', {{ dataTransfer, bubbles: true }}));
          this.dispatchEvent(new DragEvent('dragend', {{ dataTransfer, bubbles: true }}));
      }};
  
      // Perform drag and drop
      source.dragTo(target);
      // Final click on canvas to confirm drop
      target.click();
    }}
    """)

def connect_nodes(page: Page, connection: dict) -> None:
    """
    Connects a port from a source node to a port on a target node.

    :param page: The Playwright page object.
    :param connection: A dictionary with the following keys:
        - sourceNode: Name of the source node (e.g. "Literal String")
        - sourcePort: Name of the source port (e.g. "out-0")
        - targetNode: Name of the target node (e.g. "GradioInterface")
        - targetPort: Name of the target port (e.g. "parameter-dynalist-parameterNames")
    """
    print(f"Connecting {connection['sourceNode']} (port {connection['sourcePort']}) "
          f"to {connection['targetNode']} (port {connection['targetPort']})...")
    result = page.evaluate(f"""
    () => {{
        // Function to calculate the center of an element
        function getCenter(el) {{
            const rect = el.getBoundingClientRect();
            return {{ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 }};
        }}

        // Target the source port based on node name and port
        const sourcePort = document.querySelector("div.node[data-default-node-name='{connection['sourceNode']}'] div.port[data-name='{connection['sourcePort']}']");
        // Try to find the target port inside a node, or fallback to a global port if not found inside
        let targetPort = document.querySelector("div.node[data-default-node-name='{connection['targetNode']}'] div.port[data-name='{connection['targetPort']}']");

        console.log("Source port:", sourcePort);
        console.log("Target port:", targetPort);

        if (!sourcePort || !targetPort) {{
            console.warn("Source or target port not found.");
            return false;
        }}

        const from = getCenter(sourcePort);
        const to = getCenter(targetPort);
        const dataTransfer = new DataTransfer();

        function fireEvent(el, type, clientX, clientY) {{
            const event = new DragEvent(type, {{
                bubbles: true,
                cancelable: true,
                composed: true,
                clientX: clientX,
                clientY: clientY,
                dataTransfer: dataTransfer
            }});
            el.dispatchEvent(event);
        }}

        fireEvent(sourcePort, "mousedown", from.x, from.y);
        fireEvent(document, "mousemove", (from.x + to.x) / 2, (from.y + to.y) / 2);
        fireEvent(document, "mousemove", to.x, to.y);
        fireEvent(targetPort, "mouseup", to.x, to.y);

        return true;
    }}
    """)

    if result:
        print(f"{connection['sourceNode']} successfully connected to {connection['targetNode']}.")
    else:
        print("Failed to connect. Check canvas_debug.html for details.")

    if result:
        print(f"{connection['sourceNode']} successfully connected to {connection['targetNode']}.")
    else:
        print("Failed to connect. Check canvas_debug.html for details.")

def lock_component(page, component_name: str):
    """
    Attempts to toggle the lock of the specified component by directly dispatching a click event
    on its lock toggle element.
    
    :param page: Playwright Page object.
    :param component_name: The name of the component as shown in data-default-node-name attribute.
    """
    print(f"Locking component: {component_name} ...")
    
    result = page.evaluate(f"""
    () => {{
        const node = Array.from(document.querySelectorAll("div.node"))
                       .find(el => el.getAttribute("data-default-node-name") === "{component_name}");
        if (!node) {{
            console.warn("Component '{component_name}' not found.");
            return false;
        }}
        const lockToggle = node.querySelector("div.react-toggle.lock");
        if (!lockToggle) {{
            console.warn("Lock toggle for '{component_name}' not found.");
            return false;
        }}
        lockToggle.click();
        return true;
    }}
    """)
    
    if result:
        print(f"Lock toggled for {component_name}.")
    else:
        print(f"Failed to toggle lock for {component_name}.")

def simulate_zoom_ctrl_wheel(page: Page, zoom_in: bool = True, delta: int = 120) -> None:
    """
    Simulates zooming in or out using Ctrl + mouse wheel,
    with mouse movement over the canvas first.
    
    :param page: The Playwright Page object.
    :param zoom_in: True to zoom in, False to zoom out.
    :param delta: Scroll delta in pixels; use negative for zoom in, positive for zoom out.
    """
    print("Moving mouse to the canvas area...")
    page.hover(".xircuits-canvas")
    
    if zoom_in:
        print("Simulating zoom in using Ctrl + mouse wheel (scroll up).")
        page.keyboard.down("Control")
        page.mouse.wheel(0, -delta)  
        page.keyboard.up("Control")
    else:
        print("Simulating zoom out using Ctrl + mouse wheel (scroll down).")
        page.keyboard.down("Control")
        page.mouse.wheel(0, delta)   
        page.keyboard.up("Control")

def compile_and_run_workflow(page):
    page.locator('button[title="Save (Ctrl+S)"]').click()
    page.locator('button[title="Compile Xircuits"]').click()
    page.locator('button[title="Compile and Run Xircuits"]').click()

def connect_nodes_simple(page: Page, connection: dict) -> None:
    """
    Connects a port from the source node to a port on the target node
    using mouse events and hover simulation, similar to TypeScript behavior.

    :param page: The Playwright page object.
    :param connection: A dictionary containing the following keys:
        - sourceNode: Name of the source node
        - sourcePort: Name of the source port
        - targetNode: Name of the target node
        - targetPort: Name of the target port
    """
    print(f"Connecting {connection['sourceNode']} ({connection['sourcePort']}) --> {connection['targetNode']} ({connection['targetPort']})")

    # Hover over the source port
    source_locator = page.locator(f'div[data-default-node-name="{connection["sourceNode"]}"] >> div[data-name="{connection["sourcePort"]}"]')
    source_locator.hover()
    page.wait_for_timeout(100)

    # Press mouse button to start dragging
    page.mouse.down()

    # Hover over the target port
    target_locator = page.locator(f'div[data-default-node-name="{connection["targetNode"]}"] >> div[data-name="{connection["targetPort"]}"]')
    target_locator.hover()
    page.wait_for_timeout(100)

    # Release mouse button to drop the connection
    page.mouse.up()

    print("Connection simulated.")

def delete_component_simple(page: Page, node_name: str) -> None:
    """
    Deletes a visible component from the canvas by simulating click and pressing Delete key.

    :param page: Playwright page object.
    :param node_name: Node name as shown in data-default-node-name.
    """
    print(f"Deleting component '{node_name}' via click and Delete key...")

    # Scroll and click the node
    node = page.locator(f"div.node[data-default-node-name='{node_name}']")
    node.scroll_into_view_if_needed()
    node.click()

    # Press Delete
    page.keyboard.press("Delete")
    print(f"Component '{node_name}' deletion triggered.")

def define_argument_parameter(page: Page, value: str):
    """
    Waits for the parameter input dialog, fills it with the given value, and submits.

    :param page: Playwright page object.
    :param value: The name to define for the argument parameter.
    """
    print(f"Defining argument parameter: {value}")
    page.wait_for_selector("input[name='Please define parameter']")
    page.fill("input[name='Please define parameter']", value)
    page.click("div.jp-Dialog-buttonLabel:has-text('Submit')")
    page.click(".xircuits-canvas")
    page.wait_for_timeout(500)

def assert_all_texts_exist(page: Page, words: list[str]):
    missing = [word for word in words if page.locator(f"text={word}").count() == 0]
    assert not missing, f"The following texts were not found: {missing}"

def delete_component_directly(page: Page, node_name: str) -> None:
    """
    Deletes a component from the canvas directly using JavaScript without needing it to be visible.

    :param page: The Playwright page object.
    :param node_name: The node name as in data-default-node-name.
    """
    print(f"Attempting to delete component: {node_name} programmatically (without visibility)...")

    result = page.evaluate(f"""
    () => {{
        const target = document.querySelector("div.node[data-default-node-name='{node_name}']");
        if (!target) {{
            console.warn("Component not found in DOM.");
            return false;
        }}

        function getCenter(el) {{
            const rect = el.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2
            }};
        }}

        const center = getCenter(target);

        // Simulate mouse events to select the element, then delete it via keyboard event
        const mouseDown = new MouseEvent('mousedown', {{
            bubbles: true,
            cancelable: true,
            clientX: center.x,
            clientY: center.y
        }});
        const mouseUp = new MouseEvent('mouseup', {{
            bubbles: true,
            cancelable: true,
            clientX: center.x,
            clientY: center.y
        }});
        target.dispatchEvent(mouseDown);
        target.dispatchEvent(mouseUp);

        // Dispatch Delete key event on document
        const deleteEvent = new KeyboardEvent('keydown', {{
            key: 'Delete',
            code: 'Delete',
            keyCode: 46,
            which: 46,
            bubbles: true,
            cancelable: true
        }});
        document.dispatchEvent(deleteEvent);

        return true;
    }}
    """)

    if result:
        print(f"Component '{node_name}' deleted (if supported by canvas logic).")
    else:
        print(f"Failed to delete component '{node_name}'. Check DOM or logic.")